from app.adapters.inbound.api.meters_router import router as meters_router
from app.adapters.inbound.api.anomalies_router import router as anomalies_router
from app.adapters.inbound.api.dashboard_router import router as dashboard_router
from app.adapters.inbound.api.ai_router import router as ai_router
from app.adapters.inbound.api.assistant_router import router as assistant_router

__all__ = [
    "meters_router",
    "anomalies_router",
    "dashboard_router",
    "ai_router",
    "assistant_router",
]
