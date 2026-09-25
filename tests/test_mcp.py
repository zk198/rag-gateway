import pytest
from fastmcp import Client

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
