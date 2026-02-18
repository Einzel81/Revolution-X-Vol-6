"""
AI Code Guardian - Performance Monitor
مراقب الأداء الذكي للبوت
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import aiohttp
from collections import deque
import json

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class MetricSnapshot:
    timestamp: datetime
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    expectancy: float
    latency_ms: float
    total_trades: int
    winning_trades: int
    losing_trades: int

@dataclass
class Alert:
    id: str
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold: float
    deviation_percent: float
    timestamp: datetime
    message: str
    suggested_action: str

class PerformanceMonitor:
    """
    مراقب الأداء المستمر للبوت التداولي
    """
    
    # Thresholds
    WIN_RATE_THRESHOLD = 0.55
    PROFIT_FACTOR_THRESHOLD = 1.5
    SHARPE_RATIO_THRESHOLD = 1.0
    MAX_DRAWDOWN_THRESHOLD = 0.15
    EXPECTANCY_THRESHOLD = 0.0
    LATENCY_THRESHOLD_MS = 100
    
    # Deviation threshold for alerts
    DEVIATION_THRESHOLD = 0.10
    
    def __init__(self, db_connection=None, notification_service=None):
        self.db = db_connection
        self.notifier = notification_service
        self.metrics_history: deque = deque(maxlen=10000)  # ~35 days of 5-min intervals
        self.alerts: List[Alert] = []
        self.is_running = False
        self.moving_averages = {
            'win_rate': deque(maxlen=288),  # 24 hours
            'profit_factor': deque(maxlen=288),
            'sharpe_ratio': deque(maxlen=288),
            'max_drawdown': deque(maxlen=288),
            'expectancy': deque(maxlen=288),
            'latency_ms': deque(maxlen=288)
        }
        
    async def start_monitoring(self):
        """بدء المراقبة المستمرة"""
        self.is_running = True
        while self.is_running:
            try:
                await self.collect_metrics()
                await self.detect_anomalies()
                await asyncio.sleep(300)  # كل 5 دقائق
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(60)
    
    def stop_monitoring(self):
        """إيقاف المراقبة"""
        self.is_running = False
    
    async def collect_metrics(self) -> MetricSnapshot:
        """جمع المقاييس من البوت"""
        # في الواقع: استدعاء API الداخلي للبوت
        metrics = await self._fetch_bot_metrics()
        
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            win_rate=metrics.get('win_rate', 0),
            profit_factor=metrics.get('profit_factor', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            max_drawdown=metrics.get('max_drawdown', 0),
            expectancy=metrics.get('expectancy', 0),
            latency_ms=metrics.get('latency_ms', 0),
            total_trades=metrics.get('total_trades', 0),
            winning_trades=metrics.get('winning_trades', 0),
            losing_trades=metrics.get('losing_trades', 0)
        )
        
        self.metrics_history.append(snapshot)
        
        # تحديث المتوسطات المتحركة
        self.moving_averages['win_rate'].append(snapshot.win_rate)
        self.moving_averages['profit_factor'].append(snapshot.profit_factor)
        self.moving_averages['sharpe_ratio'].append(snapshot.sharpe_ratio)
        self.moving_averages['max_drawdown'].append(snapshot.max_drawdown)
        self.moving_averages['expectancy'].append(snapshot.expectancy)
        self.moving_averages['latency_ms'].append(snapshot.latency_ms)
        
        # حفظ في قاعدة البيانات
        await self._save_to_db(snapshot)
        
        return snapshot
    
    async def _fetch_bot_metrics(self) -> Dict[str, float]:
        """جلب المقاييس من البوت الفعلي"""
        # TODO: ربط مع Trading Core API
        return {
            'win_rate': 0.58,
            'profit_factor': 1.8,
            'sharpe_ratio': 1.2,
            'max_drawdown': 0.12,
            'expectancy': 0.05,
            'latency_ms': 85,
            'total_trades': 150,
            'winning_trades': 87,
            'losing_trades': 63
        }
    
    async def detect_anomalies(self) -> List[Alert]:
        """اكتشاف الانحرافات عن المعدل الطبيعي"""
        if len(self.metrics_history) < 288:  # نحتاج 24 ساعة على الأقل
            return []
        
        current = self.metrics_history[-1]
        alerts = []
        
        # فحص كل مقياس
        checks = [
            ('win_rate', current.win_rate, self.WIN_RATE_THRESHOLD, '>', 
             f"انخفاض نسبة الصفقات الرابحة إلى {current.win_rate:.1%}"),
            ('profit_factor', current.profit_factor, self.PROFIT_FACTOR_THRESHOLD, '>',
             f"انخفاض معامل الربح إلى {current.profit_factor:.2f}"),
            ('sharpe_ratio', current.sharpe_ratio, self.SHARPE_RATIO_THRESHOLD, '>',
             f"انخفاض نسبة شارب إلى {current.sharpe_ratio:.2f}"),
            ('max_drawdown', current.max_drawdown, self.MAX_DRAWDOWN_THRESHOLD, '<',
             f"ارتفاع التراجع الأقصى إلى {current.max_drawdown:.1%}"),
            ('latency_ms', current.latency_ms, self.LATENCY_THRESHOLD_MS, '<',
             f"ارتفاع التأخر إلى {current.latency_ms}ms")
        ]
        
        for metric_name, current_val, threshold, direction, msg in checks:
            # حساب المتوسط المتحرك
            ma_values = list(self.moving_averages[metric_name])
            if len(ma_values) < 12:  # ساعة واحدة على الأقل
                continue
            
            ma_avg = statistics.mean(ma_values[:-1])  # exclude current
            if ma_avg == 0:
                continue
            
            deviation = abs(current_val - ma_avg) / ma_avg
            
            if deviation > self.DEVIATION_THRESHOLD:
                # تحديد مستوى الخطورة
                level = AlertLevel.WARNING if deviation < 0.20 else AlertLevel.CRITICAL
                
                # التحقق من تجاوز العتبة
                threshold_breached = False
                if direction == '>' and current_val < threshold:
                    threshold_breached = True
                elif direction == '<' and current_val > threshold:
                    threshold_breached = True
                
                if threshold_breached or deviation > 0.15:
                    alert = Alert(
                        id=f"{metric_name}_{int(datetime.utcnow().timestamp())}",
                        level=level,
                        metric_name=metric_name,
                        current_value=current_val,
                        threshold=threshold,
                        deviation_percent=deviation * 100,
                        timestamp=datetime.utcnow(),
                        message=msg,
                        suggested_action=self._get_suggested_action(metric_name, current_val)
                    )
                    alerts.append(alert)
                    await self.send_alert(alert)
        
        self.alerts.extend(alerts)
        return alerts
    
    def _get_suggested_action(self, metric_name: str, value: float) -> str:
        """الحصول على الإجراء المقترح بناءً على المقياس"""
        actions = {
            'win_rate': 'مراجعة منطق الدخول والخروج، فحص شروط الاستراتيجية',
            'profit_factor': 'تعديل نسب المخاطرة/العائد، مراجعة إدارة رأس المال',
            'sharpe_ratio': 'تقليل التقلب، إضافة فلاتر للدخول',
            'max_drawdown': 'تفعيل وقف الخسارة الأقصى، تقليل حجم المراكز',
            'latency_ms': 'فحص اتصال الإنترنت، مراجعة VPS/الخادم'
        }
        return actions.get(metric_name, 'مراجعة عامة للنظام')
    
    async def send_alert(self, alert: Alert):
        """إرسال تنبيه"""
        # حفظ في DB
        await self._save_alert_to_db(alert)
        
        # إرسال إشعار
        if self.notifier:
            await self.notifier.send({
                'type': 'guardian_alert',
                'level': alert.level.value,
                'message': alert.message,
                'metric': alert.metric_name,
                'value': alert.current_value,
                'deviation': alert.deviation_percent,
                'action': alert.suggested_action
            })
        
        # طباعة للـ logs
        print(f"[{alert.level.value.upper()}] {alert.message} "
              f"(Deviation: {alert.deviation_percent:.1f}%)")
    
    async def get_current_status(self) -> Dict[str, Any]:
        """الحصول على الحالة الحالية"""
        if not self.metrics_history:
            return {'status': 'initializing', 'message': 'جمع البيانات...'}
        
        current = self.metrics_history[-1]
        recent_alerts = [a for a in self.alerts 
                        if a.timestamp > datetime.utcnow() - timedelta(hours=24)]
        
        critical_count = sum(1 for a in recent_alerts if a.level == AlertLevel.CRITICAL)
        
        status = 'healthy'
        if critical_count > 0:
            status = 'critical'
        elif len(recent_alerts) > 3:
            status = 'warning'
        
        return {
            'status': status,
            'last_check': current.timestamp.isoformat(),
            'metrics': {
                'win_rate': current.win_rate,
                'profit_factor': current.profit_factor,
                'sharpe_ratio': current.sharpe_ratio,
                'max_drawdown': current.max_drawdown,
                'expectancy': current.expectancy,
                'latency_ms': current.latency_ms
            },
            'alerts_24h': len(recent_alerts),
            'critical_alerts': critical_count,
            'total_trades': current.total_trades
        }
    
    async def _save_to_db(self, snapshot: MetricSnapshot):
        """حفظ المقاييس في قاعدة البيانات"""
        if not self.db:
            return
        # TODO: Implement DB save
    
    async def _save_alert_to_db(self, alert: Alert):
        """حفظ التنبيه في قاعدة البيانات"""
        if not self.db:
            return
        # TODO: Implement DB save
    
    def get_metrics_report(self, hours: int = 24) -> Dict[str, Any]:
        """تقرير المقاييس لفترة زمنية"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [m for m in self.metrics_history if m.timestamp > cutoff]
        
        if not recent:
            return {'error': 'لا توجد بيانات كافية'}
        
        return {
            'period_hours': hours,
            'data_points': len(recent),
            'win_rate': {
                'current': recent[-1].win_rate,
                'avg': statistics.mean([m.win_rate for m in recent]),
                'min': min([m.win_rate for m in recent]),
                'max': max([m.win_rate for m in recent])
            },
            'profit_factor': {
                'current': recent[-1].profit_factor,
                'avg': statistics.mean([m.profit_factor for m in recent])
            },
            'sharpe_ratio': {
                'current': recent[-1].sharpe_ratio,
                'avg': statistics.mean([m.sharpe_ratio for m in recent])
            },
            'max_drawdown': {
                'current': recent[-1].max_drawdown,
                'max_observed': max([m.max_drawdown for m in recent])
            }
        }
