from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    limit: int = Field(default=10, ge=1, le=20)


class SearchResult(BaseModel):
    chunk_id: str | None = None
    parent_kind: str | None = None
    score: float | None = None
    text: str | None = None
    source_name: str | None = None
    parent: dict[str, Any] | None = None


class Source(BaseModel):
    name: str
    account_email: str | None = None
    account_type: str | None = None
    display_name: str | None = None
    description: str | None = None


class GatewaySettings(BaseModel):
    retrieval_url: str
    ingestion_url: str
    timeout_seconds: float = 60.0
    max_tool_result_chars: int = 20_000
