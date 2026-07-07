from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path
from typing import Any

from app.auth.email import EmailService, get_email_service
from app.core.config import Settings, get_settings
from app.mcp.schemas import AggregateFilters, AttemptFilters
from app.repositories.research_repo import ResearchRepository
from app.services.research_data import ResearchDataService

SEND_MAGIC_LINK = "send_magic_link"
GENERATE_RESEARCH_EXPORT = "generate_research_export"


def _email_service(ctx: dict[str, Any]) -> EmailService:
    email = ctx.get("email_service")
    if email is not None:
        return email
    return get_email_service()


def _settings(ctx: dict[str, Any]) -> Settings:
    settings = ctx.get("settings")
    if settings is not None:
        return settings
    return get_settings()


async def send_magic_link(ctx: dict[str, Any], to_email: str, link: str) -> None:
    await _email_service(ctx).send_magic_link(to_email, link)


def _research_service(session, settings: Settings) -> ResearchDataService:
    return ResearchDataService(
        ResearchRepository(session, settings.RESEARCH_PSEUDONYM_PEPPER),
        settings.RESEARCH_PSEUDONYM_PEPPER,
        settings.PGCRYPTO_KEY,
        settings.LOGIN_HASH_PEPPER,
        settings.K_ANON_THRESHOLD,
    )


async def build_research_export(
    service: ResearchDataService, filters: dict[str, Any]
) -> dict[str, Any]:
    attempts = await service.list_attempts(AttemptFilters(**filters))
    aggregate = await service.aggregate_stats(
        AggregateFilters(
            **{
                key: value
                for key, value in filters.items()
                if key in {"cohort_slug", "case_slug", "language", "mode"}
            }
        )
    )
    cohorts = await service.list_cohorts()
    return {
        "filters": filters,
        "attempts": attempts.model_dump(mode="json"),
        "aggregate": aggregate.model_dump(mode="json"),
        "cohorts": cohorts.model_dump(mode="json"),
    }


def _attempts_csv(export: dict[str, Any]) -> str:
    buffer = io.StringIO()
    fields = [
        "attempt_ref",
        "student_pseudo",
        "case_slug",
        "cohort_slug",
        "language",
        "mode",
        "phase",
        "status",
        "started_on",
        "completed_on",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for item in export["attempts"].get("items", []):
        writer.writerow(item)
    return buffer.getvalue()


async def generate_research_export(
    ctx: dict[str, Any], filters: dict[str, Any] | None = None
) -> dict[str, Any]:
    settings = _settings(ctx)
    filters = filters or {}
    sessionmaker = ctx.get("sessionmaker")
    if sessionmaker is not None:
        async with sessionmaker() as session:
            export = await build_research_export(
                _research_service(session, settings), filters
            )
    else:
        session = ctx["session"]
        export = await build_research_export(
            _research_service(session, settings), filters
        )

    export_dir = Path(settings.RESEARCH_EXPORT_DIR)
    export_dir.mkdir(parents=True, exist_ok=True)
    handle = uuid.uuid4().hex
    json_path = export_dir / f"research-export-{handle}.json"
    csv_path = export_dir / f"research-export-{handle}.csv"
    json_path.write_text(json.dumps(export, indent=2, sort_keys=True))
    csv_path.write_text(_attempts_csv(export))
    return {
        "handle": handle,
        "json_path": str(json_path),
        "csv_path": str(csv_path),
        "attempt_count": export["attempts"].get("total", 0),
        "suppressed": export["attempts"].get("suppressed", False),
    }
