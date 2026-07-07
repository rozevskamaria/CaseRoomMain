from __future__ import annotations

from contextlib import asynccontextmanager

from app.core.config import Settings
from app.mcp.auth import MCPAuthMiddleware
from app.mcp.server import build_mcp_server
from app.services.research_pseudonym import assert_pepper_distinct


def build_mcp_app(settings: Settings, session_factory):
    assert_pepper_distinct(
        settings.RESEARCH_PSEUDONYM_PEPPER,
        settings.PGCRYPTO_KEY,
        settings.LOGIN_HASH_PEPPER,
    )
    server = build_mcp_server(settings, session_factory)
    app = server.streamable_http_app()
    guarded = MCPAuthMiddleware(app, settings.MCP_RESEARCH_TOKEN)
    return guarded, server


@asynccontextmanager
async def mcp_lifespan(server):
    async with server.session_manager.run():
        yield
