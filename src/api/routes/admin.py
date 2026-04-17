"""Admin endpoints for vector database synchronization and management"""
import logging
from fastapi import APIRouter, status

from src.services.sync_service import perform_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/sync", status_code=status.HTTP_200_OK)
async def trigger_sync_endpoint():
    """
    Manually trigger synchronization from PostgreSQL → Weaviate
    
    **Admin Endpoint** - Syncs all entities from PostgreSQL to vector database
    
    Returns:
        dict: Statistics about the sync operation
            - processed: Total entities processed
            - success: Successfully indexed
            - failed: Failed to index
            - errors: List of error messages
    """
    logger.info("Manual sync triggered")
    stats = perform_sync()
    
    return {
        "status": "sync_complete",
        "processed": stats["processed"],
        "success": stats["success"],
        "failed": stats["failed"],
        "errors": stats["errors"]
    }


@router.get("/health", status_code=status.HTTP_200_OK)
async def admin_health():
    """Admin health check endpoint"""
    return {"status": "healthy", "service": "braincell-admin"}
