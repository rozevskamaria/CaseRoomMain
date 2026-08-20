from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.attempt import Attempt
from app.models.case import Case as CaseModel, CaseVersion
from app.models.cohort import (
    Cohort,
    CohortAuditAction,
    CohortAuditLog,
    CohortMembership,
    CohortMembershipStatus,
    StaffCohort,
)
from app.models.user import User, UserRole
from app.repositories.user_repo import _decrypt, _login_hash

LOGIN_NAME_PATTERN = re.compile(r"^\d{6}$")


class AddMemberError(Exception):
    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


class CohortAccessError(Exception):
    pass


class CohortRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _slugify(self, name: str) -> str:
        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "cohort"
        return f"{base}-{uuid.uuid4().hex[:8]}"

    async def create_cohort(
        self,
        *,
        name: str,
        academic_year: str | None,
        created_by: uuid.UUID,
    ) -> Cohort:
        cohort = Cohort(
            slug=self._slugify(name),
            name=name,
            academic_year=academic_year,
            created_by=created_by,
        )
        self._session.add(cohort)
        await self._session.flush()
        self._audit(
            actor_id=created_by,
            cohort_id=cohort.id,
            subject_id=created_by,
            action=CohortAuditAction.staff_assigned,
        )
        self._session.add(StaffCohort(cohort_id=cohort.id, staff_id=created_by))
        await self._session.flush()
        return cohort

    def _audit(
        self,
        *,
        actor_id: uuid.UUID | None,
        cohort_id: uuid.UUID,
        subject_id: uuid.UUID | None,
        action: CohortAuditAction,
    ) -> None:
        self._session.add(
            CohortAuditLog(
                actor_id=actor_id,
                cohort_id=cohort_id,
                subject_id=subject_id,
                action=action,
            )
        )

    async def get(self, cohort_id: uuid.UUID) -> Cohort | None:
        return await self._session.get(Cohort, cohort_id)

    async def staff_teaches_cohort(
        self, staff_id: uuid.UUID, cohort_id: uuid.UUID
    ) -> bool:
        stmt = (
            select(StaffCohort.id)
            .where(
                StaffCohort.staff_id == staff_id,
                StaffCohort.cohort_id == cohort_id,
            )
            .limit(1)
        )
        return await self._session.scalar(stmt) is not None

    async def staff_can_read_attempt(
        self, staff_id: uuid.UUID, attempt_id: uuid.UUID
    ) -> bool:
        stmt = (
            select(Attempt.id)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(StaffCohort, StaffCohort.cohort_id == Assignment.cohort_id)
            .where(
                Attempt.id == attempt_id,
                StaffCohort.staff_id == staff_id,
            )
            .limit(1)
        )
        return await self._session.scalar(stmt) is not None

    async def member_exists(
        self, cohort_id: uuid.UUID, student_id: uuid.UUID, *, active: bool = True
    ) -> bool:
        stmt = select(CohortMembership.id).where(
            CohortMembership.cohort_id == cohort_id,
            CohortMembership.student_id == student_id,
        )
        if active:
            stmt = stmt.where(
                CohortMembership.status == CohortMembershipStatus.active
            )
        return await self._session.scalar(stmt.limit(1)) is not None

    async def add_member(
        self,
        *,
        cohort_id: uuid.UUID,
        login_name: str,
        actor_id: uuid.UUID,
    ) -> tuple[CohortMembership, User]:
        if not LOGIN_NAME_PATTERN.match(login_name):
            raise AddMemberError("invalid_format")
        login_hash = await self._session.scalar(select(_login_hash(login_name)))
        user = await self._session.scalar(
            select(User).where(User.login_name_hash == login_hash)
        )
        if user is None:
            raise AddMemberError("not_found")
        if user.role != UserRole.student:
            raise AddMemberError("not_a_student")
        existing = await self._session.scalar(
            select(CohortMembership).where(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.student_id == user.id,
            )
        )
        if existing is not None:
            if existing.status == CohortMembershipStatus.active:
                raise AddMemberError("already_enrolled")
            existing.status = CohortMembershipStatus.active
            await self._session.flush()
            self._audit(
                actor_id=actor_id,
                cohort_id=cohort_id,
                subject_id=user.id,
                action=CohortAuditAction.reactivated,
            )
            await self._session.flush()
            return existing, user
        membership = CohortMembership(
            cohort_id=cohort_id,
            student_id=user.id,
            status=CohortMembershipStatus.active,
        )
        self._session.add(membership)
        await self._session.flush()
        self._audit(
            actor_id=actor_id,
            cohort_id=cohort_id,
            subject_id=user.id,
            action=CohortAuditAction.enrolled,
        )
        await self._session.flush()
        return membership, user

    async def lookup_member(
        self, *, cohort_id: uuid.UUID, login_name: str
    ) -> tuple[str, User | None]:
        if not LOGIN_NAME_PATTERN.match(login_name):
            return "not_found", None
        login_hash = await self._session.scalar(select(_login_hash(login_name)))
        user = await self._session.scalar(
            select(User).where(User.login_name_hash == login_hash)
        )
        if user is None:
            return "not_found", None
        if user.role != UserRole.student:
            return "not_a_student", user
        if await self.member_exists(cohort_id, user.id, active=True):
            return "already_enrolled", user
        return "enrollable", user

    async def remove_member(
        self,
        *,
        cohort_id: uuid.UUID,
        student_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> User | None:
        membership = await self._session.scalar(
            select(CohortMembership).where(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.student_id == student_id,
            )
        )
        if membership is None:
            return None
        if membership.status != CohortMembershipStatus.removed:
            membership.status = CohortMembershipStatus.removed
            await self._session.flush()
            self._audit(
                actor_id=actor_id,
                cohort_id=cohort_id,
                subject_id=student_id,
                action=CohortAuditAction.removed,
            )
            await self._session.flush()
        return await self._session.get(User, student_id)

    async def reactivate_member(
        self,
        *,
        cohort_id: uuid.UUID,
        student_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> User | None:
        membership = await self._session.scalar(
            select(CohortMembership).where(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.student_id == student_id,
            )
        )
        if membership is None:
            return None
        if membership.status != CohortMembershipStatus.active:
            membership.status = CohortMembershipStatus.active
            await self._session.flush()
            self._audit(
                actor_id=actor_id,
                cohort_id=cohort_id,
                subject_id=student_id,
                action=CohortAuditAction.reactivated,
            )
            await self._session.flush()
        return await self._session.get(User, student_id)

    async def assign_staff(
        self,
        *,
        cohort_id: uuid.UUID,
        staff_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> StaffCohort:
        user = await self._session.get(User, staff_id)
        if user is None or user.role not in (UserRole.staff, UserRole.admin):
            raise CohortAccessError("not_staff")
        existing = await self._session.scalar(
            select(StaffCohort).where(
                StaffCohort.cohort_id == cohort_id,
                StaffCohort.staff_id == staff_id,
            )
        )
        if existing is not None:
            return existing
        link = StaffCohort(cohort_id=cohort_id, staff_id=staff_id)
        self._session.add(link)
        await self._session.flush()
        self._audit(
            actor_id=actor_id,
            cohort_id=cohort_id,
            subject_id=staff_id,
            action=CohortAuditAction.staff_assigned,
        )
        await self._session.flush()
        return link

    async def list_for_staff(self, staff_id: uuid.UUID) -> list[Cohort]:
        stmt = (
            select(Cohort)
            .join(StaffCohort, StaffCohort.cohort_id == Cohort.id)
            .where(StaffCohort.staff_id == staff_id)
            .order_by(Cohort.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result)

    async def list_all(self) -> list[Cohort]:
        stmt = select(Cohort).order_by(Cohort.created_at.desc())
        result = await self._session.scalars(stmt)
        return list(result)

    async def cohorts_by_ids(
        self, cohort_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Cohort]:
        if not cohort_ids:
            return {}
        stmt = select(Cohort).where(Cohort.id.in_(cohort_ids))
        result = await self._session.scalars(stmt)
        return {cohort.id: cohort for cohort in result}

    async def student_counts(
        self, cohort_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        if not cohort_ids:
            return {}
        stmt = (
            select(CohortMembership.cohort_id, func.count())
            .where(
                CohortMembership.cohort_id.in_(cohort_ids),
                CohortMembership.status == CohortMembershipStatus.active,
            )
            .group_by(CohortMembership.cohort_id)
        )
        rows = await self._session.execute(stmt)
        return {cohort_id: count for cohort_id, count in rows}

    async def students_for_cohorts(
        self, cohort_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[tuple[CohortMembership, User]]]:
        if not cohort_ids:
            return {}
        stmt = (
            select(CohortMembership, User)
            .join(User, User.id == CohortMembership.student_id)
            .where(
                CohortMembership.cohort_id.in_(cohort_ids),
                CohortMembership.status == CohortMembershipStatus.active,
            )
            .order_by(CohortMembership.joined_at)
        )
        rows = await self._session.execute(stmt)
        out: dict[uuid.UUID, list[tuple[CohortMembership, User]]] = {
            cid: [] for cid in cohort_ids
        }
        for membership, user in rows:
            out[membership.cohort_id].append((membership, user))
        return out

    async def staff_for_cohorts(
        self, cohort_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[User]]:
        if not cohort_ids:
            return {}
        stmt = (
            select(StaffCohort.cohort_id, User)
            .join(User, User.id == StaffCohort.staff_id)
            .where(StaffCohort.cohort_id.in_(cohort_ids))
            .order_by(StaffCohort.created_at)
        )
        rows = await self._session.execute(stmt)
        out: dict[uuid.UUID, list[User]] = {cid: [] for cid in cohort_ids}
        for cohort_id, user in rows:
            out[cohort_id].append(user)
        return out

    async def member(
        self, cohort_id: uuid.UUID, student_id: uuid.UUID
    ) -> tuple[CohortMembership, User] | None:
        stmt = (
            select(CohortMembership, User)
            .join(User, User.id == CohortMembership.student_id)
            .where(
                CohortMembership.cohort_id == cohort_id,
                CohortMembership.student_id == student_id,
                CohortMembership.status == CohortMembershipStatus.active,
            )
        )
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return row[0], row[1]

    async def attempts_for_student_in_cohort(
        self, cohort_id: uuid.UUID, student_id: uuid.UUID
    ) -> list[tuple[Attempt, str]]:
        stmt = (
            select(Attempt, CaseModel.slug)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .where(
                Assignment.cohort_id == cohort_id,
                Attempt.student_id == student_id,
            )
            .order_by(Attempt.started_at.desc())
        )
        rows = await self._session.execute(stmt)
        return [(attempt, slug) for attempt, slug in rows]

    async def attempts_for_students(
        self, keys: list[tuple[uuid.UUID, uuid.UUID]]
    ) -> dict[tuple[uuid.UUID, uuid.UUID], list[tuple[Attempt, str]]]:
        if not keys:
            return {}
        out: dict[tuple[uuid.UUID, uuid.UUID], list[tuple[Attempt, str]]] = {
            key: [] for key in keys
        }
        cohort_ids = {cohort_id for cohort_id, _ in keys}
        student_ids = {student_id for _, student_id in keys}
        stmt = (
            select(Assignment.cohort_id, Attempt, CaseModel.slug)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .where(
                Assignment.cohort_id.in_(cohort_ids),
                Attempt.student_id.in_(student_ids),
            )
            .order_by(Attempt.started_at.desc())
        )
        rows = await self._session.execute(stmt)
        for cohort_id, attempt, slug in rows:
            key = (cohort_id, attempt.student_id)
            if key in out:
                out[key].append((attempt, slug))
        return out

    async def decrypt(self, cipher: bytes | None) -> str | None:
        if cipher is None:
            return None
        return await self._session.scalar(select(_decrypt(cipher)))

    async def audit_for_cohort(
        self, cohort_id: uuid.UUID
    ) -> list[CohortAuditLog]:
        stmt = (
            select(CohortAuditLog)
            .where(CohortAuditLog.cohort_id == cohort_id)
            .order_by(CohortAuditLog.created_at)
        )
        result = await self._session.scalars(stmt)
        return list(result)
