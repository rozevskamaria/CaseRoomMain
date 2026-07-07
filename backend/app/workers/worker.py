from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings

from app.auth.email import get_email_service
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.workers.jobs import generate_research_export, send_magic_link


async def _startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    ctx["settings"] = settings
    ctx["sessionmaker"] = get_sessionmaker()
    ctx["email_service"] = get_email_service()


async def _shutdown(ctx: dict[str, Any]) -> None:
    return None


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().REDIS_URL)


class WorkerSettings:
    functions = [send_magic_link, generate_research_export]
    on_startup = _startup
    on_shutdown = _shutdown
    redis_settings = _redis_settings()
