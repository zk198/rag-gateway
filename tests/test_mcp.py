import pytest
import httpx2
import jwt
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from rag_gateway import api
from rag_gateway.api import app
from rag_gateway.mcp import mcp


@pytest.mark.anyio
async def test_mcp_exposes_only_explicitly_tagged_llm_operations():
    async with Client(mcp) as client:
        tools = await client.list_tools()

    exposed = {tool.name for tool in tools}

    expected = {
        route.operation_id
        for route in app.routes
        if getattr(route, "operation_id", None)
        and "llm" in getattr(route, "tags", [])
    }

    assert exposed == expected


@pytest.mark.anyio
async def test_internal_and_state_changing_routes_are_not_mcp_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()

    exposed = {tool.name for tool in tools}

    internal_operations = {
        route.operation_id
        for route in app.routes
        if getattr(route, "operation_id", None)
        and "llm" not in getattr(route, "tags", [])
    }

    assert exposed.isdisjoint(internal_operations)
    assert exposed.isdisjoint({"ingest", "upload", "healthz", "stats"})


def test_llm_routes_are_explicit_and_reviewable():
    llm_routes = {
        (route.path, frozenset(route.methods), route.operation_id)
        for route in app.routes
        if "llm" in getattr(route, "tags", [])
    }

    assert llm_routes == {
        ("/search", frozenset({"POST"}), "search_knowledge"),
        ("/sources", frozenset({"GET"}), "list_sources"),
        ("/messages/{message_id}", frozenset({"GET"}), "get_message"),
        ("/documents/{document_id}", frozenset({"GET"}), "get_document"),
    }


@pytest.mark.anyio
async def test_generated_mcp_http_tool_forwards_bearer_context_to_fastapi(
    monkeypatch,
):
    secret = "test-secret-key-with-at-least-32-bytes!!"
    token = jwt.encode(
        {"sub": "token-user", "tenant_id": "token-tenant"},
        secret,
        algorithm="HS256",
    )
    monkeypatch.setenv("RAG_JWT_SECRET", secret)
    monkeypatch.delenv("RAG_JWKS_URL", raising=False)

    observed = {}

    async def fake_search(query, limit, tenant, user):
        observed["search"] = (query, limit, tenant, user)
        return [{"text": "ok"}]

    monkeypatch.setattr(api.service, "search", fake_search)

    mcp_app = mcp.http_app(transport="streamable-http", stateless_http=True)

    def httpx_client_factory(**kwargs):
        return httpx2.AsyncClient(
            transport=httpx2.ASGITransport(app=mcp_app),
            base_url="http://testserver",
            headers={"Authorization": f"Bearer {token}"},
            **kwargs,
        )

    transport = StreamableHttpTransport(
        "http://testserver/mcp",
        httpx_client_factory=httpx_client_factory,
    )

    async with mcp_app.lifespan(mcp_app):
        async with Client(transport) as client:
            result = await client.call_tool(
                "search_knowledge",
                {"query": "hello", "limit": 1},
            )

    assert result.data == [{"text": "ok"}]
    assert observed == {
        "search": ("hello", 1, "token-tenant", "token-user"),
    }
