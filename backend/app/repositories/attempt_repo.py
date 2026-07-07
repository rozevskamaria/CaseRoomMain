from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attempt import Attempt, AttemptStatus
from app.models.case import Language
from app.models.event import Event, EventType


@dataclass
class NewEvent:
    type: EventType
    data: dict = field(default_factory=dict)


class AttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_attempt(
        self,
        case_version_id: uuid.UUID,
        mode: str,
        language: str,
        student_id: uuid.UUID | None,
        assignment_id: uuid.UUID | None = None,
    ) -> Attempt:
        attempt = Attempt(
            case_version_id=case_version_id,
            mode=mode,
            language=Language(language),
            student_id=student_id,
            assignment_id=assignment_id,
        )
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def get_attempt(self, attempt_id: uuid.UUID) -> Attempt | None:
        return await self._session.get(Attempt, attempt_id)

    async def get_owner(self, attempt_id: uuid.UUID) -> uuid.UUID | None:
        return await self._session.scalar(
            select(Attempt.student_id).where(Attempt.id == attempt_id)
        )

    async def load_events(self, attempt_id: uuid.UUID) -> list[Event]:
        stmt = (
            select(Event)
            .where(Event.attempt_id == attempt_id)
            .order_by(Event.seq)
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def append_events(
        self, attempt_id: uuid.UUID, events: list[NewEvent]
    ) -> list[Event]:
        if not events:
            return []
        await self._session.scalar(
            select(Attempt.id).where(Attempt.id == attempt_id).with_for_update()
        )
        last_seq = await self._session.scalar(
            select(func.max(Event.seq)).where(Event.attempt_id == attempt_id)
        )
        next_seq = (last_seq or 0) + 1
        persisted: list[Event] = []
        for offset, new_event in enumerate(events):
            row = Event(
                attempt_id=attempt_id,
                seq=next_seq + offset,
                type=new_event.type,
                data=new_event.data,
            )
            self._session.add(row)
            persisted.append(row)
        await self._session.flush()
        return persisted

    async def update_projection_cache(
        self,
        attempt_id: uuid.UUID,
        phase: str,
        status: str,
        mode: str,
        completed_at: datetime | None,
    ) -> None:
        attempt = await self._session.get(Attempt, attempt_id)
        if attempt is None:
            return
        attempt.phase = phase
        attempt.status = AttemptStatus(status)
        attempt.mode = mode
        attempt.completed_at = completed_at
        await self._session.flush()
