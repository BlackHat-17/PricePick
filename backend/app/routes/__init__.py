"""
API routes for PricePick backend
"""

from .products import router as products_router
from .prices import router as prices_router

from .monitoring import router as monitoring_router

__all__ = [
    "products_router",
    "prices_router",
    "monitoring_router"
]
