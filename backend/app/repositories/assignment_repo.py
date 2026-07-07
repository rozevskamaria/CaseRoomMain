from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.case import Language
from app.models.cohort import CohortMembership, CohortMembershipStatus


class AssignmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        cohort_id: uuid.UUID,
        case_id: uuid.UUID,
        case_version_id: uuid.UUID,
        mode: str,
        language: str,
        title: str | None,
        opens_at: datetime | None,
        due_at: datetime | None,
        created_by: uuid.UUID | None,
    ) -> Assignment:
        assignment = Assignment(
            cohort_id=cohort_id,
            case_id=case_id,
            case_version_id=case_version_id,
            mode=mode,
            language=Language(language),
            title=title,
            opens_at=opens_at,
            due_at=due_at,
            created_by=created_by,
        )
        self._session.add(assignment)
        await self._session.flush()
        return assignment

    async def get(self, assignment_id: uuid.UUID) -> Assignment | None:
        return await self._session.get(Assignment, assignment_id)

    async def list_for_cohort(self, cohort_id: uuid.UUID) -> list[Assignment]:
        stmt = (
            select(Assignment)
            .where(Assignment.cohort_id == cohort_id)
            .order_by(Assignment.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def for_cohorts(
        self, cohort_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[Assignment]]:
        if not cohort_ids:
            return {}
        stmt = (
            select(Assignment)
            .where(Assignment.cohort_id.in_(cohort_ids))
            .order_by(Assignment.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        out: dict[uuid.UUID, list[Assignment]] = {cid: [] for cid in cohort_ids}
        for assignment in result:
            out[assignment.cohort_id].append(assignment)
        return out

    async def list_for_student(self, student_id: uuid.UUID) -> list[Assignment]:
        stmt = (
            select(Assignment)
            .join(
                CohortMembership,
                CohortMembership.cohort_id == Assignment.cohort_id,
            )
            .where(
                CohortMembership.student_id == student_id,
                CohortMembership.status == CohortMembershipStatus.active,
            )
            .order_by(Assignment.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result)
