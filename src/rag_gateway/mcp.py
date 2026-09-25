from fastmcp import FastMCP
from fastmcp.server.providers.openapi import MCPType, RouteMap

from .api import app

# Only routes explicitly tagged "llm" become MCP tools.
# The catch-all EXCLUDE prevents future REST endpoints from becoming tools.
mcp = FastMCP.from_fastapi(
    app=app,
    name="RAG Gateway",
    route_maps=[
        RouteMap(tags={"llm"}, mcp_type=MCPType.TOOL),
        RouteMap(mcp_type=MCPType.EXCLUDE),
    ],
)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
