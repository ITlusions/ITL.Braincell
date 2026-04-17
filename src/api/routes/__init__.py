"""Route modules — entity routes are auto-discovered via MemoryCell plugins."""
import logging

from fastapi import APIRouter

from . import admin, health, search
from src.cells import discover_cells

logger = logging.getLogger(__name__)


def create_routes() -> APIRouter:
    """Create and register all route modules, including auto-discovered cells."""
    router = APIRouter()

    # Core infrastructure routes
    router.include_router(health.router, tags=["health"])
    router.include_router(search.router, prefix="/api/search", tags=["search"])
    router.include_router(admin.router, tags=["admin"])

    # Auto-discovered MemoryCell routes
    for cell in discover_cells():
        router.include_router(cell.get_router(), prefix=cell.prefix, tags=cell.tags)
        logger.info("Registered cell: %s -> %s", cell.name, cell.prefix)

    return router
