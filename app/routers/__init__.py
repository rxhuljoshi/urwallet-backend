# API Routers
from .auth import router as auth_router
from .user import router as user_router
from .transactions import router as transactions_router
from .dashboard import router as dashboard_router
from .ai import router as ai_router
from .currency import router as currency_router

__all__ = [
    "auth_router",
    "user_router",
    "transactions_router",
    "dashboard_router",
    "ai_router",
    "currency_router",
]

