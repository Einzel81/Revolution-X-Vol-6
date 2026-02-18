"""
Trade Alerts - Real-time trade notifications
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.app.core.database import get_db
from backend.app.models.trade import Trade
from backend.app.models.user import User
from backend.app.telegram.bot import telegram_bot
from backend.app.services.notification_service import notification_service, NotificationPriority, NotificationChannel

logger = logging.getLogger(__name__)


class TradeAlertManager:
    """Manage trade-related alerts"""
    
    async def notify_new_trade(self, trade: Trade, user_id: int, chart_image: Optional[bytes] = None):
        """Send new trade
