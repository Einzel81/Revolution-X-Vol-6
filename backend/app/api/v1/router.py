# backend/app/api/v1/router.py (مُحدَّث)
from fastapi import APIRouter

from app.api.v1 import trading
from app.auth.router import router as auth_router

api_router = APIRouter()

api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
