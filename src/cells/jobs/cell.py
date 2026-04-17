"""Jobs memory cell — Weaviate-only, no PostgreSQL entities."""
from fastapi import APIRouter

from src.cells.base import MemoryCell


class JobsCell(MemoryCell):
    """Memory cell for job postings — stores and searches jobs via Weaviate vector DB."""

    @property
    def name(self) -> str:
        return "jobs"

    @property
    def prefix(self) -> str:
        return "/api/jobs"

    def get_router(self) -> APIRouter:
        from src.cells.jobs.routes import router
        return router

    def get_models(self) -> list:
        return []  # Weaviate-only, no SQL tables

    def register_mcp_tools(self, mcp) -> None:
        from datetime import datetime, timezone
        from src.core.database import SessionLocal
        from src.services.weaviate_service import get_weaviate_service as _gwvs
        from src.cells.interactions.model import Interaction
        from src.cells.conversations.model import Conversation
        from src.cells.decisions.model import DesignDecision
        from src.cells.architecture_notes.model import ArchitectureNote
        from src.cells.notes.model import Note
        from src.cells.snippets.model import CodeSnippet
        from src.cells.files_discussed.model import FileDiscussed
        from src.cells.sessions.model import MemorySession

        CELL_MAP = [
            ("Interaction", Interaction),
            ("Conversation", Conversation),
            ("Decision", DesignDecision),
            ("ArchitectureNote", ArchitectureNote),
            ("Note", Note),
            ("CodeSnippet", CodeSnippet),
            ("FileDiscussed", FileDiscussed),
            ("MemorySession", MemorySession),
        ]

        @mcp.tool()
        async def memory_cleanup() -> dict:
            """Archive expired PostgreSQL records to Weaviate and delete them from PostgreSQL.

            Run this daily (or on demand) to maintain the layered memory model:
            - Active records live in PostgreSQL + Weaviate (archived=false)
            - After expiry: PostgreSQL record is deleted, Weaviate vector is marked archived=true
            - Archived vectors remain searchable forever as semantic long-term memory

            Returns a summary of archived and deleted counts per collection.
            """
            wv = _gwvs()
            now = datetime.now(timezone.utc)
            stats = {}
            db = SessionLocal()
            try:
                for collection_name, Model in CELL_MAP:
                    expired = db.query(Model).filter(
                        Model.expires_at.isnot(None),
                        Model.expires_at < now,
                    ).all()
                    archived = 0
                    deleted = 0
                    for row in expired:
                        try:
                            wv.archive_object(collection_name, str(row.id))
                            archived += 1
                        except Exception:
                            pass
                        db.delete(row)
                        deleted += 1
                    db.commit()
                    stats[collection_name] = {"archived": archived, "deleted": deleted}
            finally:
                db.close()
            return {"success": True, "stats": stats, "ran_at": now.isoformat()}


cell = JobsCell()
