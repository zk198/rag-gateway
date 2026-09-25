from unittest.mock import AsyncMock

import pytest

from rag_gateway import mcp


@pytest.mark.asyncio
async def test_mcp_search_requires_bearer(monkeypatch):
    monkeypatch.setattr(mcp, "get_http_headers", lambda **_: {})
    with pytest.raises(PermissionError, match="Bearer"):
        await mcp.search_knowledge("hello", 5)


@pytest.mark.asyncio
async def test_mcp_search_uses_authenticated_identity(monkeypatch):
    monkeypatch.setattr(mcp, "get_http_headers", lambda **_: {"authorization": "Bearer token"})
    monkeypatch.setattr(mcp, "authenticate_token", lambda token: ("t1", "u1"))
    monkeypatch.setattr(mcp.service, "search", AsyncMock(return_value=[{"text": "hit"}]))
    result = await mcp.search_knowledge({"query": "hello", "limit": 5})
    assert result == [{"text": "hit"}]
    mcp.service.search.assert_awaited_once_with("hello", 5, "t1", "u1")
