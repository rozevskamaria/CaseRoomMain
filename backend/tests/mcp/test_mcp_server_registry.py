from __future__ import annotations

from app.core.config import Settings
from app.mcp.server import build_mcp_server

READ_TOOLS = {
    "list_attempts",
    "get_attempt_timeline",
    "get_feedback",
    "list_cohorts",
    "aggregate_stats",
}

MUTATION_HINTS = (
    "create",
    "update",
    "delete",
    "set_",
    "append",
    "write",
    "submit",
    "insert",
    "remove",
    "advance",
)


def _settings() -> Settings:
    return Settings(
        MCP_ENABLED=True,
        MCP_RESEARCH_TOKEN="t",
        RESEARCH_PSEUDONYM_PEPPER="distinct-research-pepper",
        PGCRYPTO_KEY="pg",
        LOGIN_HASH_PEPPER="lp",
    )


async def test_server_registers_exactly_the_five_read_tools():
    server = build_mcp_server(_settings(), session_factory=None)
    tools = await server.list_tools()
    names = {tool.name for tool in tools}
    assert names == READ_TOOLS


async def test_server_registers_no_mutation_tool():
    server = build_mcp_server(_settings(), session_factory=None)
    tools = await server.list_tools()
    for tool in tools:
        lowered = tool.name.lower()
        for hint in MUTATION_HINTS:
            assert hint not in lowered, f"mutation-looking tool {tool.name}"
