"""Route modules for all entity types"""
from fastapi import APIRouter

# Import all route modules
from . import conversations, interactions, decisions, architecture_notes, files, snippets, sessions, search, health, admin, jobs

def create_routes() -> APIRouter:
    """Create and register all route modules"""
    router = APIRouter()
    
    # Include health check
    router.include_router(health.router, tags=["health"])
    
    # Include entity routes
    router.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
    router.include_router(interactions.router, prefix="/api/interactions", tags=["interactions"])
    router.include_router(decisions.router, prefix="/api/decisions", tags=["decisions"])
    router.include_router(architecture_notes.router, prefix="/api/architecture-notes", tags=["architecture-notes"])
    router.include_router(files.router, prefix="/api/files", tags=["files"])
    router.include_router(snippets.router, prefix="/api/snippets", tags=["snippets"])
    router.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    router.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    
    # Include search routes
    router.include_router(search.router, prefix="/api/search", tags=["search"])
    
    # Include admin routes
    router.include_router(admin.router, tags=["admin"])
    
    return router
