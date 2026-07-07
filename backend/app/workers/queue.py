from __future__ import annotations

from app.services.jobs import (
    ArqJobQueue,
    InMemoryJobQueue,
    JobQueue,
)
from app.workers.jobs import (
    GENERATE_RESEARCH_EXPORT,
    SEND_MAGIC_LINK,
    generate_research_export,
    send_magic_link,
)

_INMEMORY_FUNCTIONS = {
    SEND_MAGIC_LINK: send_magic_link,
    GENERATE_RESEARCH_EXPORT: generate_research_export,
}

_job_queue: JobQueue | None = None


def make_inmemory_queue() -> InMemoryJobQueue:
    return InMemoryJobQueue(dict(_INMEMORY_FUNCTIONS))


def configure_inmemory() -> InMemoryJobQueue:
    global _job_queue
    queue = make_inmemory_queue()
    _job_queue = queue
    return queue


def configure_production(pool) -> ArqJobQueue:
    global _job_queue
    queue = ArqJobQueue(pool)
    _job_queue = queue
    return queue


async def create_arq_pool():
    from arq import create_pool
    from arq.connections import RedisSettings

    from app.core.config import get_settings

    return await create_pool(RedisSettings.from_dsn(get_settings().REDIS_URL))


def set_job_queue(queue: JobQueue | None) -> None:
    global _job_queue
    _job_queue = queue


def get_job_queue() -> JobQueue:
    global _job_queue
    if _job_queue is None:
        _job_queue = make_inmemory_queue()
    return _job_queue


def reset() -> None:
    global _job_queue
    _job_queue = None
