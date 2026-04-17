"""BrainCell Dashboard - Web Application

Standalone web dashboard for viewing BrainCell memory system.
Provides UI for conversations, decisions, architecture notes, code snippets, and search.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from src.core.config import get_settings
from src.core.database import init_db
from src.web.router import router as dashboard_router

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
    logger.info("BrainCell Dashboard - Starting up")
    logger.info(f"Environment: {settings.environment}")
    logger.info("=" * 60)
    
    try:
        init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization error: {e}")
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("BrainCell Dashboard - Shutting down gracefully")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title="BrainCell Dashboard",
    version=settings.api_version,
    description="Web dashboard for BrainCell memory system",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs for dashboard
    openapi_url=None,  # Disable OpenAPI schema
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, images)
web_dir = Path(__file__).parent
static_dir = web_dir / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir)), name="assets")
    logger.info(f"✓ Static files mounted from {static_dir}")

# Register dashboard routes
app.include_router(dashboard_router)

# Redirect root to dashboard
@app.get("/")
async def root():
    """Redirect root to dashboard"""
    return RedirectResponse(url="/dashboard/")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
