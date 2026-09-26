from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.providers.openapi import MCPType, RouteMap

from .api import app
from .auth import reset_mcp_authorization, set_mcp_authorization


class AuthorizationContextMiddleware(Middleware):
    """Bridge the inbound MCP bearer token to generated FastAPI tools.

    FastMCP intentionally excludes Authorization from headers forwarded by its
    OpenAPI provider. The generated tool still executes the FastAPI route in
    process, so keep the existing JWT verifier as the single authentication
    implementation and expose only the request-scoped bearer header to it.
    """

    async def on_request(self, context: MiddlewareContext, call_next):
        headers = get_http_headers(include={"authorization"})
        token = set_mcp_authorization(headers.get("authorization"))
        try:
            return await call_next(context)
        finally:
            reset_mcp_authorization(token)


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
mcp.add_middleware(AuthorizationContextMiddleware())


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
