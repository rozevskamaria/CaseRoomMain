from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Protocol


class JobQueue(Protocol):
    async def enqueue(self, job_name: str, **kwargs: Any) -> Any: ...


@dataclass
class EnqueuedJob:
    job_name: str
    kwargs: dict[str, Any]


JobFunction = Callable[..., Awaitable[Any]]


class InMemoryJobQueue:
    def __init__(
        self, functions: dict[str, JobFunction] | None = None
    ) -> None:
        self.jobs: list[EnqueuedJob] = []
        self._functions = functions or {}

    async def enqueue(self, job_name: str, **kwargs: Any) -> EnqueuedJob:
        job = EnqueuedJob(job_name=job_name, kwargs=dict(kwargs))
        self.jobs.append(job)
        return job

    async def run_pending(self, ctx: dict[str, Any] | None = None) -> None:
        context = ctx or {}
        while self.jobs:
            job = self.jobs.pop(0)
            fn = self._functions.get(job.job_name)
            if fn is None:
                continue
            await fn(context, **job.kwargs)


class ArqJobQueue:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def enqueue(self, job_name: str, **kwargs: Any) -> Any:
        return await self._pool.enqueue_job(job_name, **kwargs)
