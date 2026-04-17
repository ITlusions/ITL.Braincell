"""Interactions memory cell."""
from fastapi import APIRouter

from src.cells.base import MemoryCell


class InteractionsCell(MemoryCell):
    """Memory cell for interactions — individual messages within conversations."""

    @property
    def name(self) -> str:
        return "interactions"

    @property
    def prefix(self) -> str:
        return "/api/interactions"

    def get_router(self) -> APIRouter:
        from src.cells.interactions.routes import router
        return router

    def get_models(self) -> list:
        from src.cells.interactions.model import Interaction
        return [Interaction]

    def register_mcp_tools(self, mcp) -> None:
        from src.core.database import SessionLocal
        from src.cells.interactions.model import Interaction

        @mcp.tool()
        async def interactions_search(query: str, limit: int = 10) -> dict:
            """Search individual messages or chat turns by content or speaker role.

            Use when looking for what was specifically said in a message, a particular
            user request, or an assistant response. Matches on the raw message text
            and role (user/assistant/system).
            Not for conversation-level topics — use conversations_search instead.
            """
            db = SessionLocal()
            try:
                # Try Weaviate vector search first
                wv_hits = []
                try:
                    from src.services.weaviate_service import get_weaviate_service as _gwvs
                    wv_hits = _gwvs().search_interactions(query, limit=limit * 2)
                except Exception:
                    pass
                if wv_hits:
                    from uuid import UUID as _UUID
                    live_ids = [h["embedding_id"] for h in wv_hits if not h.get("archived") and h.get("embedding_id")]
                    archived_list = [
                        {"id": h.get("embedding_id"), "archived": True,
                         "role": h.get("role"), "content": (h.get("content") or "")[:200],
                         "message_type": h.get("message_type")}
                        for h in wv_hits if h.get("archived")
                    ]
                    rows = db.query(Interaction).filter(
                        Interaction.id.in_([_UUID(i) for i in live_ids if i])
                    ).limit(limit).all()
                    return {"query": query, "count": len(rows) + len(archived_list),
                            "results": [{"id": str(r.id), "role": r.role, "content": (r.content or "")[:200], "message_type": r.message_type} for r in rows],
                            "archived": archived_list}
                # Fallback: ILIKE
                q = query.lower()
                rows = db.query(Interaction).filter(
                    Interaction.content.ilike(f"%{q}%") | Interaction.role.ilike(f"%{q}%")
                ).limit(limit).all()
                return {"query": query, "count": len(rows), "results": [
                    {"id": str(r.id), "role": r.role,
                     "content": (r.content or "")[:200], "message_type": r.message_type}
                    for r in rows
                ]}
            finally:
                db.close()

        @mcp.tool()
        async def interactions_save(
            role: str,
            content: str,
            message_type: str | None = None,
            conversation_id: str | None = None,
            session_id: str | None = None,
            retention_days: int | None = None,
            retain_reason: str | None = None,
        ) -> dict:
            """Save a single message or chat turn to memory.

            Use when recording an individual user/assistant exchange, a tool output,
            or any raw message-level content. role must be 'user', 'assistant', or 'system'.
            For a whole conversation summary use conversations_save.
            For a session-level summary use sessions_save.
            """
            if not role or not content:
                return {"error": "role and content are required"}
            from uuid import UUID
            from src.services.retention_policy import evaluate as _retention
            retention = _retention("interactions", {"role": role, "content": content})
            if retention_days is not None:
                retention.retention_days = retention_days
            if retain_reason is not None:
                retention.reason = retain_reason
            if not retention.should_save:
                return {"saved": False, "reason": retention.reason}
            db = SessionLocal()
            try:
                interaction = Interaction(
                    role=role, content=content, message_type=message_type,
                    conversation_id=UUID(conversation_id) if conversation_id else None,
                    session_id=UUID(session_id) if session_id else None,
                    retention_days=retention.retention_days,
                    retain_reason=retention.reason,
                    expires_at=retention.expires_at,
                )
                db.add(interaction)
                db.commit()
                db.refresh(interaction)
                try:
                    from src.services.weaviate_service import get_weaviate_service as _gwvs
                    _gwvs().index_interaction(
                        str(interaction.id), content=content, role=role,
                        message_type=message_type or "",
                        conversation_id=conversation_id,
                        session_id=session_id,
                    )
                except Exception:
                    pass
                return {"success": True, "id": str(interaction.id), "retention_days": retention.retention_days, "retain_reason": retention.reason}
            finally:
                db.close()

        @mcp.tool()
        async def interactions_list(limit: int = 50) -> dict:
            """List recent individual messages across all conversations, newest first.

            Use to review raw chat history at the message level.
            For conversation summaries use conversations_list.
            """
            db = SessionLocal()
            try:
                rows = db.query(Interaction).order_by(
                    Interaction.created_at.desc()
                ).limit(limit).all()
                return {"count": len(rows), "items": [
                    {"id": str(r.id), "role": r.role,
                     "content": (r.content or "")[:100], "message_type": r.message_type}
                    for r in rows
                ]}
            finally:
                db.close()


cell = InteractionsCell()
