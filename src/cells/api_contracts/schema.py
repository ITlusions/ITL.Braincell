"""ApiContract Pydantic schemas."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ApiContractCreate(BaseModel):
    title: str
    service_name: str
    version: str
    base_url: str | None = None
    spec_format: str | None = None
    spec_content: str | None = None
    status: str = "active"
    breaking_changes: str | None = None
    changelog: list[dict[str, Any]] | None = None
    endpoints: list[dict[str, Any]] | None = None
    auth_type: str | None = None
    tags: list[str] | None = None
    meta_data: dict[str, Any] | None = None


class ApiContractResponse(ApiContractCreate):
    id: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
    retention_days: int | None = None

    class Config:
        from_attributes = True
