"""BrainCell API - Main application entry point

Centralized memory system for GitHub Copilot with:
- Real-time vector database synchronization
- Semantic search across all entity types
- Design decision tracking
- Architecture documentation
- Code snippet management
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.database import init_db
from src.services.weaviate_service import get_weaviate_service
from src.services.sync_service import perform_sync
from src.api.routes import create_routes
from src.cells import discover_cells

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management - startup and shutdown"""
    # Startup
    logger.info("=" * 60)
    logger.info("BrainCell API - Starting up")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)

    # Discover cells and import their models before init_db() so that
    # SQLAlchemy's Base.metadata includes cell tables.
    cells = discover_cells()
    for cell in cells:
        cell.get_models()  # triggers model module import

    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")

    # Check Weaviate connectivity
    weaviate = get_weaviate_service()
    if weaviate.health_check():
        logger.info("✓ Weaviate vector database connected")

        # Perform initial sync of all entities from PostgreSQL to Weaviate
        logger.info("Starting vector database synchronization...")
        try:
            stats = perform_sync()
            logger.info(f"✓ Vector database sync complete: {stats['success']} indexed, {stats['failed']} failed")
            if stats['failed'] > 0:
                logger.warning(f"Sync had {stats['failed']} failures - check logs for details")
        except Exception as e:
            logger.error(f"✗ Vector database sync failed: {e}")

        # Run per-cell startup hooks
        from src.core.database import SessionLocal
        db = SessionLocal()
        try:
            for cell in cells:
                try:
                    cell_stats = cell.on_startup(db, weaviate)
                    if cell_stats:
                        logger.info(f"Cell '{cell.name}' startup: {cell_stats}")
                except Exception as exc:
                    logger.error(f"Cell '{cell.name}' startup hook failed: {exc}")
        finally:
            db.close()
    else:
        logger.warning("⚠ Weaviate health check failed - semantic search may be unavailable")

    yield

    # Shutdown
    logger.info("=" * 60)
    logger.info("BrainCell API - Shutting down gracefully")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Centralized memory system for GitHub Copilot with real-time vector sync and semantic search",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
routes = create_routes()
app.include_router(routes)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
