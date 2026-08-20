from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.models.assignment import Assignment
from app.models.cohort import Cohort, CohortAuditLog
from app.models.user import User
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.case_repo import CaseRepository
from app.repositories.cohort_repo import (
    AddMemberError,
    CohortAccessError,
    CohortRepository,
)


@dataclass
class RosterRow:
    user: User
    cohort_id: uuid.UUID
    joined_at: datetime


@dataclass
class StudentLookup:
    status: str
    user: User | None


@dataclass
class AddMemberOutcome:
    cohort: Cohort
    student: User


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class CohortService:
    def __init__(
        self,
        cohorts: CohortRepository,
        assignments: AssignmentRepository,
        cases: CaseRepository,
    ) -> None:
        self._cohorts = cohorts
        self._assignments = assignments
        self._cases = cases

    async def staff_can_read_attempt(
        self, staff_id: str, attempt_id: str
    ) -> bool:
        return await self._cohorts.staff_can_read_attempt(
            _as_uuid(staff_id), _as_uuid(attempt_id)
        )

    async def staff_teaches_cohort(self, staff_id: str, cohort_id: str) -> bool:
        return await self._cohorts.staff_teaches_cohort(
            _as_uuid(staff_id), _as_uuid(cohort_id)
        )

    async def create_cohort(
        self, *, name: str, academic_year: str | None, created_by: str
    ) -> Cohort:
        return await self._cohorts.create_cohort(
            name=name,
            academic_year=academic_year,
            created_by=_as_uuid(created_by),
        )

    async def get_cohort(self, cohort_id: str) -> Cohort | None:
        return await self._cohorts.get(_as_uuid(cohort_id))

    async def add_member(
        self, *, cohort_id: str, login_name: str, actor_id: str
    ) -> AddMemberOutcome:
        cohort = await self._cohorts.get(_as_uuid(cohort_id))
        if cohort is None:
            raise AddMemberError("not_found")
        _, user = await self._cohorts.add_member(
            cohort_id=_as_uuid(cohort_id),
            login_name=login_name,
            actor_id=_as_uuid(actor_id),
        )
        return AddMemberOutcome(cohort=cohort, student=user)

    async def lookup_student(
        self, *, cohort_id: str, login_name: str
    ) -> StudentLookup:
        status, user = await self._cohorts.lookup_member(
            cohort_id=_as_uuid(cohort_id), login_name=login_name
        )
        return StudentLookup(status=status, user=user)

    async def remove_member(
        self, *, cohort_id: str, student_id: str, actor_id: str
    ) -> AddMemberOutcome:
        cohort = await self._cohorts.get(_as_uuid(cohort_id))
        if cohort is None:
            raise AddMemberError("not_found")
        user = await self._cohorts.remove_member(
            cohort_id=_as_uuid(cohort_id),
            student_id=_as_uuid(student_id),
            actor_id=_as_uuid(actor_id),
        )
        if user is None:
            raise AddMemberError("not_found")
        return AddMemberOutcome(cohort=cohort, student=user)

    async def assign_staff(
        self, *, cohort_id: str, staff_id: str, actor_id: str
    ) -> Cohort:
        cohort = await self._cohorts.get(_as_uuid(cohort_id))
        if cohort is None:
            raise CohortAccessError("not_found")
        await self._cohorts.assign_staff(
            cohort_id=_as_uuid(cohort_id),
            staff_id=_as_uuid(staff_id),
            actor_id=_as_uuid(actor_id),
        )
        return cohort

    async def list_for_staff(self, staff_id: str) -> list[Cohort]:
        return await self._cohorts.list_for_staff(_as_uuid(staff_id))

    async def list_all(self) -> list[Cohort]:
        return await self._cohorts.list_all()

    async def cohorts_for_users(
        self, user_ids: list[str], *, admin: bool
    ) -> dict[str, list[Cohort]]:
        if admin:
            cohorts = await self._cohorts.list_all()
            return {uid: list(cohorts) for uid in user_ids}
        out: dict[str, list[Cohort]] = {}
        for uid in user_ids:
            out[uid] = await self._cohorts.list_for_staff(_as_uuid(uid))
        return out

    async def cohorts_by_id(
        self, cohort_ids: list[str]
    ) -> dict[str, Cohort | None]:
        resolved = await self._cohorts.cohorts_by_ids(
            [_as_uuid(cid) for cid in cohort_ids]
        )
        return {cid: resolved.get(_as_uuid(cid)) for cid in cohort_ids}

    async def students_for_cohorts(
        self, cohort_ids: list[str]
    ) -> dict[str, list[RosterRow]]:
        resolved = await self._cohorts.students_for_cohorts(
            [_as_uuid(cid) for cid in cohort_ids]
        )
        out: dict[str, list[RosterRow]] = {}
        for cid in cohort_ids:
            rows = resolved.get(_as_uuid(cid), [])
            out[cid] = [
                RosterRow(
                    user=user,
                    cohort_id=membership.cohort_id,
                    joined_at=membership.joined_at,
                )
                for membership, user in rows
            ]
        return out

    async def staff_for_cohorts(
        self, cohort_ids: list[str]
    ) -> dict[str, list[User]]:
        resolved = await self._cohorts.staff_for_cohorts(
            [_as_uuid(cid) for cid in cohort_ids]
        )
        return {cid: resolved.get(_as_uuid(cid), []) for cid in cohort_ids}

    async def assignments_for_cohorts(
        self, cohort_ids: list[str]
    ) -> dict[str, list[Assignment]]:
        resolved = await self._assignments.for_cohorts(
            [_as_uuid(cid) for cid in cohort_ids]
        )
        return {cid: resolved.get(_as_uuid(cid), []) for cid in cohort_ids}

    async def attempts_for_students(
        self, keys: list[tuple[str, str]]
    ) -> dict[tuple[str, str], list]:
        uuid_keys = [(_as_uuid(c), _as_uuid(s)) for c, s in keys]
        resolved = await self._cohorts.attempts_for_students(uuid_keys)
        out: dict[tuple[str, str], list] = {}
        for (cohort_id, student_id), (uc, us) in zip(keys, uuid_keys, strict=True):
            out[(cohort_id, student_id)] = resolved.get((uc, us), [])
        return out

    async def member_active(self, cohort_id: str, student_id: str) -> bool:
        return await self._cohorts.member_exists(
            _as_uuid(cohort_id), _as_uuid(student_id), active=True
        )

    async def get_member(
        self, cohort_id: str, student_id: str
    ) -> RosterRow | None:
        found = await self._cohorts.member(
            _as_uuid(cohort_id), _as_uuid(student_id)
        )
        if found is None:
            return None
        membership, user = found
        return RosterRow(
            user=user, cohort_id=membership.cohort_id, joined_at=membership.joined_at
        )

    async def student_attempts(
        self, cohort_id: str, student_id: str
    ) -> list:
        return await self._cohorts.attempts_for_student_in_cohort(
            _as_uuid(cohort_id), _as_uuid(student_id)
        )

    async def assignments_for_cohort(self, cohort_id: str) -> list[Assignment]:
        return await self._assignments.list_for_cohort(_as_uuid(cohort_id))

    async def audit_for_cohort(self, cohort_id: str) -> list[CohortAuditLog]:
        return await self._cohorts.audit_for_cohort(_as_uuid(cohort_id))

    async def create_assignment(
        self,
        *,
        cohort_id: str,
        case_id: str,
        mode: str,
        language: str,
        title: str | None,
        opens_at: datetime | None,
        due_at: datetime | None,
        created_by: str,
    ) -> Assignment:
        case = await self._cases.get_case_by_slug(case_id)
        if case is None:
            raise CohortAccessError("unknown_case")
        version = await self._cases.get_case_version(case_id)
        if version is None:
            raise CohortAccessError("unpublished_case")
        return await self._assignments.create(
            cohort_id=_as_uuid(cohort_id),
            case_id=version.case_id,
            case_version_id=version.id,
            mode=mode,
            language=language,
            title=title,
            opens_at=opens_at,
            due_at=due_at,
            created_by=_as_uuid(created_by),
        )

    async def get_assignment(self, assignment_id: str) -> Assignment | None:
        return await self._assignments.get(_as_uuid(assignment_id))

    async def decrypt(self, cipher: bytes | None) -> str | None:
        return await self._cohorts.decrypt(cipher)
