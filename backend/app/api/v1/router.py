from fastapi import APIRouter

from .trading import router as trading_router
from .ai import router as ai_router
from .guardian import router as guardian_router
from .webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(trading_router, prefix="/trading", tags=["trading"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(guardian_router, prefix="/guardian", tags=["guardian"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
