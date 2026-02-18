"""
API Endpoints for AI Code Guardian
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.core.auth import get_current_user, require_admin
from backend.app.guardian.monitor import PerformanceMonitor
from backend.app.guardian.analyzer import CodeAnalyzer
from backend.app.guardian.fixer import AutoFixer
from backend.app.guardian.models import (
    PerformanceMetric, Alert, CodeChange, GuardianState,
    GuardianStatus, ChangeStatus
)
from backend.app.guardian.knowledge_base import KnowledgeBase

router = APIRouter(prefix="/guardian", tags=["guardian"])

# Dependency to get monitor instance
def get_monitor(db: Session = Depends(get_db)):
    return PerformanceMonitor(db)

def get_analyzer(db: Session = Depends(get_db)):
    return CodeAnalyzer(db)

def get_fixer(db: Session = Depends(get_db)):
    return AutoFixer(db)

def get_knowledge(db: Session = Depends(get_db)):
    return KnowledgeBase(db)

# Response Models
class StatusResponse(BaseModel):
    status: str
    last_check: datetime
    active_models: List[str]
    pending_changes_count: int
    active_alerts_count: int
    uptime_hours: float

class MetricsResponse(BaseModel):
    current: PerformanceMetric
    history: List[PerformanceMetric]

class AlertResponse(BaseModel):
    alerts: List[Alert]
    total: int
    critical: int

class ChangeApprovalRequest(BaseModel):
    approved: bool
    comment: Optional[str] = None

# Endpoints

@router.get("/status", response_model=StatusResponse)
async def get_guardian_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على حالة Guardian"""
    monitor = PerformanceMonitor(db)
    fixer = AutoFixer(db)
    
    pending = len(fixer.get_pending_changes())
    alerts = len(monitor.get_active_alerts())
    
    return StatusResponse(
        status=GuardianStatus.OPERATIONAL.value,
        last_check=datetime.utcnow(),
        active_models=["gpt-4", "performance_monitor"],
        pending_changes_count=pending,
        active_alerts_count=alerts,
        uptime_hours=720.5  # TODO: حساب فعلي
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على المقاييس"""
    from backend.app.guardian.models import PerformanceMetricDB
    
    metrics = db.query(PerformanceMetricDB).order_by(
        PerformanceMetricDB.timestamp.desc()
    ).limit(limit).all()
    
    current = metrics[0] if metrics else None
    
    return MetricsResponse(
        current=PerformanceMetric.from_orm(current) if current else None,
        history=[PerformanceMetric.from_orm(m) for m in metrics]
    )

@router.get("/alerts", response_model=AlertResponse)
async def get_alerts(
    severity: Optional[str] = None,
    resolved: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """الحصول على التنبيهات"""
    from backend.app.guardian.models import AlertDB
    
    query = db.query(AlertDB)
    
    if severity:
        query = query.filter(AlertDB.severity == severity)
    if resolved is not None:
        query = query.filter(AlertDB.is_resolved == resolved)
        
    alerts = query.order_by(AlertDB.timestamp.desc()).all()
    
    critical = sum(1 for a in alerts if a.severity == "critical")
    
    return AlertResponse(
        alerts=[Alert.from_orm(a) for a in alerts],
        total=len(alerts),
        critical=critical
    )

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """حل تنبيه
