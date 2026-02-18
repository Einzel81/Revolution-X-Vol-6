"""
Main API Router - Phase 4 Updated
"""

from fastapi import APIRouter

from .trading import router as trading_router
from .ai import router as ai_router  # Add this

router = APIRouter()

router.include_router(trading_router, prefix="/trading", tags=["Trading"])
router.include_router(ai_router, prefix="/ai", tags=["AI System"])  # Add this
