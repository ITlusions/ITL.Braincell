"""Health check endpoints"""
import logging
from fastapi import APIRouter

from src.core.config import get_settings
from src.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check():
    """Health check endpoint - returns service status"""
    weaviate = get_weaviate_service()
    return {
        "status": "ok",
        "weaviate": weaviate.health_check(),
        "environment": settings.environment
    }
