from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from .auth import authenticate_token
from .api import service

mcp = FastMCP("RAG Gateway")


def _identity() -> tuple[str, str]:
    headers = get_http_headers(include={"authorization"})
    header = headers.get("authorization", "")
    if not header.startswith("Bearer ") or not header[7:].strip():
        raise PermissionError("Bearer token required")
    return authenticate_token(header[7:].strip())


@mcp.tool(name="search_knowledge")
async def search_knowledge(query: str, limit: int = 10) -> list[dict]:
    """Search the user's authorized private knowledge base."""
    tenant, user = _identity()
    return await service.search(query, limit, tenant, user)


@mcp.tool(name="list_sources")
async def list_sources() -> list[dict]:
    """List knowledge sources available to the authenticated user."""
    tenant, user = _identity()
    return await service.get_sources(tenant, user)


@mcp.tool(name="get_message")
async def get_message(message_id: str) -> dict:
    """Get an authorized email/message by ID."""
    tenant, user = _identity()
    return await service.get_message(message_id, tenant, user)


@mcp.tool(name="get_document")
async def get_document(document_id: str) -> dict:
    """Get an authorized document by ID."""
    tenant, user = _identity()
    return await service.get_document(document_id, tenant, user)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
