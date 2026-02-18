"""
Revolution X - Prometheus Metrics
Application performance monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client.exposition import generate_latest
from fastapi import Request, Response
import time
from typing import Callable

from app.core.config import settings


# Create registry
registry = CollectorRegistry()

# Application info
app_info = Info(
    "revolutionx_app",
    "Application information",
    registry=registry
)
app_info.info({
    "version": settings.APP_VERSION,
    "environment": settings.ENVIRONMENT,
    "name": "Revolution X"
})

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry
)

# Active connections
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
    registry=registry
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
    registry=registry
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Idle database connections",
    registry=registry
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry
)

# Trading metrics
trades_executed_total = Counter(
    "trades_executed_total",
    "Total trades executed",
    ["symbol", "side", "strategy"],
    registry=registry
)

trade_volume_total = Counter(
    "trade_volume_total",
    "Total trading volume",
    ["symbol"],
    registry=registry
)

trade_pnl = Gauge(
    "trade_pnl",
    "Trade profit/loss",
    ["symbol", "trade_id"],
    registry=registry
)

open_positions = Gauge(
    "open_positions",
    "Number of open positions",
    ["symbol"],
    registry=registry
)

# AI metrics
ai_predictions_total = Counter(
    "ai_predictions_total",
    "Total AI predictions made",
   
