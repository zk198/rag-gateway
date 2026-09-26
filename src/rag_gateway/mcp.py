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

# Mount the Streamable HTTP MCP app at /mcp. Because the parent application
# supplies the /mcp prefix, the nested FastMCP app must use path="/".
# Its lifespan is also attached to the parent so the MCP session manager is
# initialized when the combined FastAPI application starts.
mcp_app = mcp.http_app(path="/", transport="streamable-http", stateless_http=True)
app.router.lifespan_context = mcp_app.lifespan
app.mount("/mcp", mcp_app)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)
