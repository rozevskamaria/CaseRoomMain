from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.schemas.case import Case
from app.services.projection import (
    AttemptProjection,
    EventRecord,
    EventType,
    NewEvent,
)


@dataclass
class AttemptMeta:
    started_at: datetime
    completed_at: datetime | None
    status: str


class AttemptStore(Protocol):
    async def create_attempt(
        self,
        case_version_ref: str,
        mode: str,
        language: str,
        student_id: str | None,
        assignment_id: str | None = None,
    ) -> str: ...

    async def load_events(self, attempt_id: str) -> list[EventRecord]: ...

    async def load_events_many(
        self, attempt_ids: list[str]
    ) -> dict[str, list[EventRecord]]: ...

    async def append_events(
        self, attempt_id: str, events: list[NewEvent]
    ) -> list[EventRecord]: ...

    async def get_attempt_owner(self, attempt_id: str) -> str | None: ...

    async def get_attempt_meta(self, attempt_id: str) -> AttemptMeta | None: ...

    async def sync_projection(
        self, attempt_id: str, proj: AttemptProjection
    ) -> None: ...


def _projection_status(proj: AttemptProjection) -> str:
    return "completed" if proj.feedback is not None else "in_progress"


class CaseSource(Protocol):
    async def get_case(self, slug: str, language: str = "en") -> Case | None: ...


class InMemoryAttemptStore:
    def __init__(self) -> None:
        self._events: dict[str, list[EventRecord]] = {}
        self._meta: dict[str, dict] = {}

    async def create_attempt(
        self,
        case_version_ref: str,
        mode: str,
        language: str,
        student_id: str | None,
        assignment_id: str | None = None,
    ) -> str:
        attempt_id = str(uuid.uuid4())
        self._events[attempt_id] = []
        self._meta[attempt_id] = {
            "case_version_ref": case_version_ref,
            "mode": mode,
            "language": language,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "status": "in_progress",
        }
        return attempt_id

    async def load_events(self, attempt_id: str) -> list[EventRecord]:
        return list(self._events.get(attempt_id, []))

    async def load_events_many(
        self, attempt_ids: list[str]
    ) -> dict[str, list[EventRecord]]:
        return {
            attempt_id: list(self._events.get(attempt_id, []))
            for attempt_id in attempt_ids
        }

    async def get_attempt_owner(self, attempt_id: str) -> str | None:
        meta = self._meta.get(attempt_id)
        if meta is None:
            return None
        return meta.get("student_id")

    async def get_attempt_meta(self, attempt_id: str) -> AttemptMeta | None:
        meta = self._meta.get(attempt_id)
        if meta is None:
            return None
        return AttemptMeta(
            started_at=meta["started_at"],
            completed_at=meta["completed_at"],
            status=meta["status"],
        )

    async def sync_projection(
        self, attempt_id: str, proj: AttemptProjection
    ) -> None:
        meta = self._meta.get(attempt_id)
        if meta is None:
            return
        status = _projection_status(proj)
        meta["mode"] = proj.mode
        meta["status"] = status
        if status == "completed" and meta["completed_at"] is None:
            meta["completed_at"] = datetime.now(timezone.utc)

    async def append_events(
        self, attempt_id: str, events: list[NewEvent]
    ) -> list[EventRecord]:
        log = self._events.setdefault(attempt_id, [])
        next_seq = (log[-1].seq + 1) if log else 1
        persisted: list[EventRecord] = []
        for offset, new_event in enumerate(events):
            etype = new_event.type
            record = EventRecord(
                type=etype.value if isinstance(etype, EventType) else etype,
                seq=next_seq + offset,
                data=new_event.data,
            )
            log.append(record)
            persisted.append(record)
        return persisted


class RegistryCaseSource:
    async def get_case(self, slug: str, language: str = "en") -> Case | None:
        from app.content.cases import get_case

        return get_case(slug)


class DbAttemptStore:
    def __init__(self, attempt_repo, case_repo) -> None:
        self._repo = attempt_repo
        self._case_repo = case_repo

    async def create_attempt(
        self,
        case_version_ref: str,
        mode: str,
        language: str,
        student_id: str | None,
        assignment_id: str | None = None,
    ) -> str:
        version = await self._case_repo.get_case_version(case_version_ref)
        if version is None:
            raise KeyError(case_version_ref)
        attempt = await self._repo.create_attempt(
            case_version_id=version.id,
            mode=mode,
            language=language,
            student_id=uuid.UUID(student_id) if student_id is not None else None,
            assignment_id=(
                uuid.UUID(assignment_id) if assignment_id is not None else None
            ),
        )
        return str(attempt.id)

    async def load_events(self, attempt_id: str) -> list[EventRecord]:
        rows = await self._repo.load_events(uuid.UUID(attempt_id))
        return [
            EventRecord(type=row.type.value, seq=row.seq, data=row.data)
            for row in rows
        ]

    async def load_events_many(
        self, attempt_ids: list[str]
    ) -> dict[str, list[EventRecord]]:
        grouped = await self._repo.load_events_many(
            [uuid.UUID(attempt_id) for attempt_id in attempt_ids]
        )
        return {
            str(attempt_id): [
                EventRecord(type=row.type.value, seq=row.seq, data=row.data)
                for row in rows
            ]
            for attempt_id, rows in grouped.items()
        }

    async def get_attempt_owner(self, attempt_id: str) -> str | None:
        owner = await self._repo.get_owner(uuid.UUID(attempt_id))
        return str(owner) if owner is not None else None

    async def get_attempt_meta(self, attempt_id: str) -> AttemptMeta | None:
        attempt = await self._repo.get_attempt(uuid.UUID(attempt_id))
        if attempt is None:
            return None
        return AttemptMeta(
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            status=attempt.status.value,
        )

    async def sync_projection(
        self, attempt_id: str, proj: AttemptProjection
    ) -> None:
        status = _projection_status(proj)
        completed_at = (
            datetime.now(timezone.utc) if status == "completed" else None
        )
        await self._repo.update_projection_cache(
            uuid.UUID(attempt_id),
            phase=proj.phase,
            status=status,
            mode=proj.mode,
            completed_at=completed_at,
        )

    async def append_events(
        self, attempt_id: str, events: list[NewEvent]
    ) -> list[EventRecord]:
        from app.models.event import EventType as ModelEventType
        from app.repositories.attempt_repo import NewEvent as RepoNewEvent

        repo_events = [
            RepoNewEvent(type=ModelEventType(_event_value(e.type)), data=e.data)
            for e in events
        ]
        rows = await self._repo.append_events(uuid.UUID(attempt_id), repo_events)
        return [
            EventRecord(type=row.type.value, seq=row.seq, data=row.data)
            for row in rows
        ]


class DbCaseSource:
    def __init__(self, repo) -> None:
        self._repo = repo

    async def get_case(self, slug: str, language: str = "en") -> Case | None:
        return await self._repo.get_published_case(slug, language)


def build_db_service(session, llm):
    from app.repositories.attempt_repo import AttemptRepository
    from app.repositories.case_repo import CaseRepository
    from app.services.session import SessionService

    case_repo = CaseRepository(session)
    attempt_repo = AttemptRepository(session)
    return SessionService(
        llm,
        store=DbAttemptStore(attempt_repo, case_repo),
        cases=DbCaseSource(case_repo),
    )


def _event_value(etype) -> str:
    return etype.value if isinstance(etype, EventType) else etype
