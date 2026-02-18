# backend/app/api/v1/trading.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db

router = APIRouter()

@router.get("/status")
async def trading_status():
    return {
        "status": "active",
        "mode": "auto_scaling",
        "open_positions": 0,
        "daily_pnl": 0.0
    }

@router.get("/balance")
async def get_balance():
    return {
        "balance": 12450.00,
        "equity": 12595.50,
        "margin": 250.00,
        "free_margin": 12345.50
    }
