from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.core.config import Settings
from app.mcp.schemas import AggregateFilters, AttemptFilters
from app.repositories.research_repo import ResearchRepository
from app.services.research_data import ResearchDataService


def build_mcp_server(settings: Settings, session_factory) -> FastMCP:
    server = FastMCP("caseroom-research", streamable_http_path="/")

    def _service(session) -> ResearchDataService:
        return ResearchDataService(
            ResearchRepository(session, settings.RESEARCH_PSEUDONYM_PEPPER),
            settings.RESEARCH_PSEUDONYM_PEPPER,
            settings.PGCRYPTO_KEY,
            settings.LOGIN_HASH_PEPPER,
            settings.K_ANON_THRESHOLD,
        )

    @server.tool(
        name="list_attempts",
        description="List pseudonymized attempt summaries filtered by cohort, "
        "case, status, language, mode, or start date.",
    )
    async def list_attempts(filters: AttemptFilters) -> dict:
        async with session_factory()() as session:
            result = await _service(session).list_attempts(filters)
            return result.model_dump(mode="json")

    @server.tool(
        name="get_attempt_timeline",
        description="Return the scrubbed, categorical event timeline for one "
        "attempt (no free text, relative offsets only).",
    )
    async def get_attempt_timeline(attempt_ref: str) -> dict | None:
        async with session_factory()() as session:
            result = await _service(session).get_attempt_timeline(attempt_ref)
            return result.model_dump(mode="json") if result is not None else None

    @server.tool(
        name="get_feedback",
        description="Return the categorical feedback outcome (scores, "
        "diagnostic accuracy, hint count) for one attempt.",
    )
    async def get_feedback(attempt_ref: str) -> dict | None:
        async with session_factory()() as session:
            result = await _service(session).get_feedback(attempt_ref)
            return result.model_dump(mode="json") if result is not None else None

    @server.tool(
        name="list_cohorts",
        description="List cohorts with banded enrollment counts and "
        "assignment counts (no staff identity).",
    )
    async def list_cohorts(include_archived: bool = False) -> dict:
        async with session_factory()() as session:
            result = await _service(session).list_cohorts(include_archived)
            return result.model_dump(mode="json")

    @server.tool(
        name="aggregate_stats",
        description="Compute k-anonymized, count-only aggregate metrics. "
        "metric='all' requires a cohort_slug or case_slug filter.",
    )
    async def aggregate_stats(filters: AggregateFilters) -> dict:
        async with session_factory()() as session:
            result = await _service(session).aggregate_stats(filters)
            return result.model_dump(mode="json")

    return server
