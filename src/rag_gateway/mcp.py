from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.providers.openapi import MCPType, RouteMap

from .api import app
from .auth import reset_mcp_authorization, set_mcp_authorization


class AuthorizationContextMiddleware(Middleware):
    """Bridge the inbound MCP bearer token to generated FastAPI tools."""

    async def on_request(self, context: MiddlewareContext, call_next):
        headers = get_http_headers(include={"authorization"})
        token = set_mcp_authorization(headers.get("authorization"))
        try:
            return await call_next(context)
        finally:
            reset_mcp_authorization(token)


mcp = FastMCP.from_fastapi(
    app=app,
    name="RAG Gateway",
    route_maps=[
        RouteMap(tags={"llm"}, mcp_type=MCPType.TOOL),
        RouteMap(mcp_type=MCPType.EXCLUDE),
    ],
)
mcp.add_middleware(AuthorizationContextMiddleware())

# Serve the REST gateway and its MCP projection from the same HTTP service.
# The transport is explicitly Streamable HTTP and stateless for horizontal
# scalability; FastMCP 4 handles protocol negotiation for clients.
app.mount(
    "/mcp",
    mcp.http_app(transport="streamable-http", stateless_http=True),
)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
