# backend/app/auth/router.py
from __future__ import annotations

from typing import Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.core.security import security_manager
from app.models.user import User

# ??? ???? Enum ??????? ???:
# backend/app/auth/models.py -> class UserRole(str, Enum)
try:
    from app.auth.models import UserRole  # type: ignore
except Exception:
    UserRole = None  # fallback


router = APIRouter()


# -----------------------------
# Schemas (????? ??????)
# -----------------------------
class UserPublic(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool = True
    is_verified: bool = True

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def _get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    q = select(User).where(User.email == email)
    res = await db.execute(q)
    return res.scalar_one_or_none()


def _role_default() -> Any:
    """
    ????? role ??????? ????? ??? Enum ??????? ?? ???????.
    """
    if UserRole is not None:
        # ?????? TRADER ?? ?????? ??????? ???????
        return getattr(UserRole, "TRADER", list(UserRole)[0])
    # fallback string (?? ??? model ???? str)
    return "TRADER"


# -----------------------------
# Routes
# -----------------------------
@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize_email(str(data.email))
    password = data.password

    user = await _get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    if user.is_verified is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not verified",
        )

    # verify password against users.password_hash
    if not security_manager.verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = security_manager.create_access_token(
        subject=str(user.id),
        additional_claims={"role": str(user.role), "email": user.email},
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserPublic.model_validate(user),
    )


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    email = _normalize_email(str(data.email))

    existing = await _get_user_by_email(db, email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = security_manager.hash_password(data.password)

    user = User(
        email=email,
        password_hash=password_hash,
        full_name=data.full_name,
        role=_role_default(),
        is_active=True,
        is_verified=True,
        two_factor_enabled=False,
        metadata={},
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserPublic.model_validate(user)