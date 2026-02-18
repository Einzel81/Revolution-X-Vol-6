# backend/app/auth/service.py
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import pyotp
import qrcode
import io
import base64

from app.config import settings
from app.auth.models import User, Session, AuditLog, UserRole
from app.auth.schemas import (
    UserCreate, UserUpdate, LoginRequest, TokenResponse,
    PasswordChange, TwoFactorSetup, TwoFactorVerify,
    AuditLogCreate, UserResponse
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # Password utilities
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    # JWT utilities
    def create_access_token(self, user_id: UUID, role: UserRole) -> Tuple[str, datetime]:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access",
            "role": role.value
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt, expire
    
    def create_refresh_token(self, user_id: UUID) -> Tuple[str, datetime]:
        expires_delta = timedelta(days=7)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt, expire
    
    def decode_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None
    
    # User CRUD
    async def create_user(self, user_data: UserCreate) -> User:
        # Check if email exists
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Create user
        db_user = User(
            email=user_data.email,
            password_hash=self.get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            created_by=user_data.created_by
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        # Log creation
        await self.create_audit_log(
            AuditLogCreate(
                action="user_created",
                details={"email": user_data.email, "role": user_data.role.value}
            ),
            db_user.id
        )
        
        return db_user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        await self.create_audit_log(
            AuditLogCreate(action="user_updated", details=update_data),
            user_id
        )
        
        return user
    
    async def delete_user(self, user_id: UUID) -> bool:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        await self.db.delete(user)
        await self.db.commit()
        
        await self.create_audit_log(
            AuditLogCreate(action="user_deleted", details={"email": user.email}),
            user_id
        )
        return True
    
    # Authentication
    async def authenticate(self, login_data: LoginRequest) -> TokenResponse:
        user = await self.get_user_by_email(login_data.email)
        if not user:
            raise ValueError("Invalid credentials")
        
        if not user.is_active:
            raise ValueError("Account is disabled")
        
        if not self.verify_password(login_data.password, user.password_hash):
            await self.create_audit_log(
                AuditLogCreate(action="login_failed", details={"reason": "invalid_password"}),
                user.id
            )
            raise ValueError("Invalid credentials")
        
        # 2FA check
        if user.two_factor_enabled:
            if not login_data.two_factor_code:
                raise ValueError("2FA code required")
            
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(login_data.two_factor_code, valid_window=1):
                raise ValueError("Invalid 2FA code")
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        # Create tokens
        access_token, access_expire = self.create_access_token(user.id, user.role)
        refresh_token, refresh_expire = self.create_refresh_token(user.id)
        
        # Create session
        session = Session(
            user_id=user.id,
            token=refresh_token,
            expires_at=refresh_expire
        )
        self.db.add(session)
        await self.db.commit()
        
        # Log successful login
        await self.create_audit_log(
            AuditLogCreate(action="login_success"),
            user.id
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        payload = self.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        user_id = UUID(payload["sub"])
        user = await self.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            raise ValueError("Invalid token")
        
        # Check if session exists and not revoked
        result = await self.db.execute(
            select(Session).where(
                and_(Session.token == refresh_token, Session.is_revoked == False)
            )
        )
        session = result.scalar_one_or_none()
        if not session or session.expires_at < datetime.utcnow():
            raise ValueError("Session expired")
        
        # Create new tokens
        access_token, _ = self.create_access_token(user.id, user.role)
        new_refresh_token, refresh_expire = self.create_refresh_token(user.id)
        
        # Update session
        session.token = new_refresh_token
        session.expires_at = refresh_expire
        await self.db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )
    
    async def logout(self, user_id: UUID, refresh_token: str):
        result = await self.db.execute(
            select(Session).where(
                and_(Session.user_id == user_id, Session.token == refresh_token)
            )
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_revoked = True
            await self.db.commit()
        
        await self.create_audit_log(
            AuditLogCreate(action="logout"),
            user_id
        )
    
    # 2FA
    async def setup_2fa(self, user_id: UUID) -> TwoFactorSetup:
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        secret = pyotp.random_base32()
        
        # Generate QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Revolution X"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Store secret temporarily (will be confirmed)
        user.two_factor_secret = secret
        await self.db.commit()
        
        return TwoFactorSetup(
            secret=secret,
            qr_code=f"data:image/png;base64,{qr_base64}"
        )
    
    async def verify_and_enable_2fa(self, user_id: UUID, verify_data: TwoFactorVerify):
        user = await self.get_user_by_id(user_id)
        if not user or not user.two_factor_secret:
            raise ValueError("2FA not setup")
        
        totp = pyotp.TOTP(user.two_factor_secret)
        if not totp.verify(verify_data.code, valid_window=1):
            raise ValueError("Invalid code")
        
        user.two_factor_enabled = True
        await self.db.commit()
        
        await self.create_audit_log(
            AuditLogCreate(action="2fa_enabled"),
            user_id
        )
    
    # Audit logs
    async def create_audit_log(self, log_data: AuditLogCreate, user_id: Optional[UUID] = None):
        log = AuditLog(
            user_id=user_id,
            action=log_data.action,
            details=log_data.details or {},
            ip_address=log_data.ip_address
        )
        self.db.add(log)
        await self.db.commit()
    
    async def get_user_audit_logs(self, user_id: UUID, limit: int = 100):
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
