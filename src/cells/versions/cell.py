"""Versions cell — cell definition."""
from fastapi import APIRouter

from src.cells.base import MemoryCell


class VersionsCell(MemoryCell):
    """Versions cell.

    Tracks component/module version history with changelog notes.
    """

    @property
    def name(self) -> str:
        return "versions"

    @property
    def prefix(self) -> str:
        return "/api/versions"

    def get_router(self) -> APIRouter:
        from src.cells.versions.routes import router
        return router

    def get_models(self) -> list:
        from src.cells.versions.model import CellVersion
        return [CellVersion]

    def register_mcp_tools(self, mcp) -> None:
        pass


cell = VersionsCell()
