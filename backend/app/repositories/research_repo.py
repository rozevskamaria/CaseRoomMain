from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Text, bindparam, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.attempt import Attempt
from app.models.case import Case as CaseModel
from app.models.case import CaseVersion
from app.models.cohort import (
    Cohort,
    CohortMembership,
    CohortMembershipStatus,
)
from app.models.event import Event, EventType

FEEDBACK_GENERATED = EventType.FeedbackGenerated
PHASE_CHANGED = EventType.PhaseChanged
TEST_ORDERED = EventType.TestOrdered
HINT_REQUESTED = EventType.HintRequested
DIFFERENTIALS_EVALUATED = EventType.DifferentialsEvaluated
LAB_RESULT_SHOWN = EventType.LabResultShown
GENETIC_NUDGE_SHOWN = EventType.GeneticNudgeShown
EXAM_PATHOGNOMONIC_NOTED = EventType.ExamPathognomonicNoted

SCORE_DIMENSIONS = (
    "historyTaking",
    "examination",
    "differential",
    "testSelection",
    "interpretation",
    "management",
)


@dataclass(frozen=True)
class AttemptRow:
    attempt_id: uuid.UUID
    student_pseudo: str | None
    case_slug: str
    cohort_slug: str | None
    assignment_id: uuid.UUID | None
    language: str
    mode: str
    started_at: datetime
    completed_at: datetime | None
    last_phase: str | None
    has_feedback: bool


@dataclass(frozen=True)
class TimelineRow:
    type: str
    seq: int
    created_at: datetime
    data: dict


@dataclass(frozen=True)
class FeedbackRow:
    attempt_id: uuid.UUID
    student_pseudo: str | None
    case_slug: str
    cohort_slug: str | None
    diagnostic_accuracy: str | None
    scores: dict[str, str | None]
    hints_used: int


@dataclass(frozen=True)
class CohortMetaRow:
    cohort_slug: str
    name: str
    academic_year: str | None
    archived: bool
    enrolled_count: int
    assignment_count: int


@dataclass(frozen=True)
class AttemptFilterSpec:
    cohort_slug: str | None = None
    case_slug: str | None = None
    language: str | None = None
    mode: str | None = None
    started_after: datetime | None = None
    started_before: datetime | None = None


class ResearchRepository:
    def __init__(self, session: AsyncSession, pepper: str) -> None:
        self._session = session
        self._pepper = pepper

    def _pseudo_expr(self):
        return func.encode(
            func.hmac(
                cast(Attempt.student_id, Text),
                bindparam(None, self._pepper),
                "sha256",
            ),
            "hex",
        )

    def _feedback_subq(self):
        latest = (
            select(
                Event.attempt_id.label("attempt_id"),
                func.max(Event.seq).label("max_seq"),
            )
            .where(Event.type == FEEDBACK_GENERATED)
            .group_by(Event.attempt_id)
            .subquery()
        )
        return latest

    def _phase_subq(self):
        latest = (
            select(
                Event.attempt_id.label("attempt_id"),
                func.max(Event.seq).label("max_seq"),
            )
            .where(Event.type == PHASE_CHANGED)
            .group_by(Event.attempt_id)
            .subquery()
        )
        return latest

    def _apply_attempt_filters(self, stmt, spec: AttemptFilterSpec):
        if spec.cohort_slug is not None:
            stmt = stmt.where(Cohort.slug == spec.cohort_slug)
        if spec.case_slug is not None:
            stmt = stmt.where(CaseModel.slug == spec.case_slug)
        if spec.language is not None:
            stmt = stmt.where(Attempt.language == spec.language)
        if spec.mode is not None:
            stmt = stmt.where(Attempt.mode == spec.mode)
        if spec.started_after is not None:
            stmt = stmt.where(Attempt.started_at >= spec.started_after)
        if spec.started_before is not None:
            stmt = stmt.where(Attempt.started_at <= spec.started_before)
        return stmt

    def _base_attempt_join(self):
        fb = self._feedback_subq()
        ph = self._phase_subq()
        fb_event = Event.__table__.alias("fb_event")
        ph_event = Event.__table__.alias("ph_event")
        columns = [
            Attempt.id,
            self._pseudo_expr().label("student_pseudo"),
            CaseModel.slug.label("case_slug"),
            Cohort.slug.label("cohort_slug"),
            Attempt.assignment_id,
            Attempt.language,
            Attempt.mode,
            Attempt.started_at,
            fb_event.c.created_at.label("completed_at"),
            ph_event.c.data["to_phase"].astext.label("last_phase"),
            (fb_event.c.id.isnot(None)).label("has_feedback"),
        ]
        stmt = (
            select(*columns)
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .outerjoin(fb, fb.c.attempt_id == Attempt.id)
            .outerjoin(
                fb_event,
                (fb_event.c.attempt_id == fb.c.attempt_id)
                & (fb_event.c.seq == fb.c.max_seq),
            )
            .outerjoin(ph, ph.c.attempt_id == Attempt.id)
            .outerjoin(
                ph_event,
                (ph_event.c.attempt_id == ph.c.attempt_id)
                & (ph_event.c.seq == ph.c.max_seq),
            )
        )
        return stmt

    def _row_to_attempt(self, row) -> AttemptRow:
        return AttemptRow(
            attempt_id=row.id,
            student_pseudo=row.student_pseudo,
            case_slug=row.case_slug,
            cohort_slug=row.cohort_slug,
            assignment_id=row.assignment_id,
            language=_enum_value(row.language),
            mode=row.mode,
            started_at=row.started_at,
            completed_at=row.completed_at,
            last_phase=row.last_phase,
            has_feedback=bool(row.has_feedback),
        )

    async def list_attempts(
        self,
        spec: AttemptFilterSpec,
        limit: int,
        offset: int,
    ) -> list[AttemptRow]:
        stmt = self._base_attempt_join()
        stmt = self._apply_attempt_filters(stmt, spec)
        stmt = stmt.order_by(Attempt.started_at.desc()).limit(limit).offset(offset)
        rows = await self._session.execute(stmt)
        return [self._row_to_attempt(row) for row in rows]

    async def count_attempts(self, spec: AttemptFilterSpec) -> int:
        stmt = (
            select(func.count())
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        return int(await self._session.scalar(stmt) or 0)

    async def attempt_header(self, attempt_id: uuid.UUID) -> AttemptRow | None:
        stmt = self._base_attempt_join().where(Attempt.id == attempt_id)
        row = (await self._session.execute(stmt)).first()
        if row is None:
            return None
        return self._row_to_attempt(row)

    async def cohort_student_count(self, cohort_slug: str | None) -> int | None:
        if cohort_slug is None:
            return None
        stmt = (
            select(func.count(func.distinct(CohortMembership.student_id)))
            .select_from(CohortMembership)
            .join(Cohort, Cohort.id == CohortMembership.cohort_id)
            .where(
                Cohort.slug == cohort_slug,
                CohortMembership.status == CohortMembershipStatus.active,
            )
        )
        return int(await self._session.scalar(stmt) or 0)

    async def distinct_students_for_filter(self, spec: AttemptFilterSpec) -> int:
        stmt = (
            select(func.count(func.distinct(Attempt.student_id)))
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .where(Attempt.student_id.isnot(None))
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        return int(await self._session.scalar(stmt) or 0)

    async def timeline(
        self, attempt_id: uuid.UUID, limit: int
    ) -> list[TimelineRow]:
        stmt = (
            select(Event.type, Event.seq, Event.created_at, Event.data)
            .where(Event.attempt_id == attempt_id)
            .order_by(Event.seq)
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        return [
            TimelineRow(
                type=_enum_value(row.type),
                seq=row.seq,
                created_at=row.created_at,
                data=row.data or {},
            )
            for row in rows
        ]

    async def attempt_start(self, attempt_id: uuid.UUID) -> datetime | None:
        return await self._session.scalar(
            select(Attempt.started_at).where(Attempt.id == attempt_id)
        )

    async def feedback_rows(self, spec: AttemptFilterSpec) -> list[FeedbackRow]:
        fb = self._feedback_subq()
        fb_event = Event.__table__.alias("fb_event")
        scores = fb_event.c.data["feedback"]["scores"]
        accuracy = fb_event.c.data["feedback"]["diagnosticAccuracy"].astext
        hint_count = (
            select(func.count())
            .select_from(Event)
            .where(
                Event.attempt_id == Attempt.id,
                Event.type == HINT_REQUESTED,
            )
            .scalar_subquery()
        )
        columns = [
            Attempt.id,
            self._pseudo_expr().label("student_pseudo"),
            CaseModel.slug.label("case_slug"),
            Cohort.slug.label("cohort_slug"),
            accuracy.label("diagnostic_accuracy"),
            hint_count.label("hints_used"),
        ]
        for dim in SCORE_DIMENSIONS:
            columns.append(scores[dim].astext.label(f"score_{dim}"))
        stmt = (
            select(*columns)
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .join(fb, fb.c.attempt_id == Attempt.id)
            .join(
                fb_event,
                (fb_event.c.attempt_id == fb.c.attempt_id)
                & (fb_event.c.seq == fb.c.max_seq),
            )
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        out: list[FeedbackRow] = []
        for row in rows:
            mapping = row._mapping
            out.append(
                FeedbackRow(
                    attempt_id=row.id,
                    student_pseudo=row.student_pseudo,
                    case_slug=row.case_slug,
                    cohort_slug=row.cohort_slug,
                    diagnostic_accuracy=row.diagnostic_accuracy,
                    scores={
                        dim: mapping[f"score_{dim}"] for dim in SCORE_DIMENSIONS
                    },
                    hints_used=int(row.hints_used or 0),
                )
            )
        return out

    async def attempts_per_case(
        self, spec: AttemptFilterSpec
    ) -> dict[str, int]:
        stmt = (
            select(CaseModel.slug, func.count())
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .group_by(CaseModel.slug)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        return {slug: int(count) for slug, count in rows}

    async def completed_per_case(
        self, spec: AttemptFilterSpec
    ) -> dict[str, int]:
        fb = self._feedback_subq()
        stmt = (
            select(CaseModel.slug, func.count())
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .join(fb, fb.c.attempt_id == Attempt.id)
            .group_by(CaseModel.slug)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        return {slug: int(count) for slug, count in rows}

    async def wrong_path_counts(
        self, spec: AttemptFilterSpec
    ) -> list[tuple[str, str, int]]:
        wrong_key = Event.data["wrong_key"].astext
        source = Event.data["source"].astext
        stmt = (
            select(CaseModel.slug, wrong_key, func.count())
            .select_from(Event)
            .join(Attempt, Attempt.id == Event.attempt_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .where(
                Event.type == DIFFERENTIALS_EVALUATED,
                source == "wrong_path",
                wrong_key.isnot(None),
            )
            .group_by(CaseModel.slug, wrong_key)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        return [(slug, key, int(count)) for slug, key, count in rows]

    async def hint_counts_per_attempt(
        self, spec: AttemptFilterSpec
    ) -> list[tuple[str, int]]:
        hint_count = (
            select(func.count())
            .select_from(Event)
            .where(
                Event.attempt_id == Attempt.id,
                Event.type == HINT_REQUESTED,
            )
            .scalar_subquery()
        )
        stmt = (
            select(CaseModel.slug, hint_count)
            .select_from(Attempt)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        return [(slug, int(count or 0)) for slug, count in rows]

    async def clue_event_counts(
        self, spec: AttemptFilterSpec
    ) -> dict[str, dict[str, int]]:
        ordered_key = Event.data["key"].astext
        stmt = (
            select(CaseModel.slug, Event.type, ordered_key, func.count())
            .select_from(Event)
            .join(Attempt, Attempt.id == Event.attempt_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .outerjoin(Assignment, Assignment.id == Attempt.assignment_id)
            .outerjoin(Cohort, Cohort.id == Assignment.cohort_id)
            .where(
                Event.type.in_(
                    [
                        TEST_ORDERED,
                        LAB_RESULT_SHOWN,
                        GENETIC_NUDGE_SHOWN,
                        EXAM_PATHOGNOMONIC_NOTED,
                    ]
                )
            )
            .group_by(CaseModel.slug, Event.type, ordered_key)
        )
        stmt = self._apply_attempt_filters(stmt, spec)
        rows = await self._session.execute(stmt)
        out: dict[str, dict[str, int]] = {}
        for slug, etype, key, count in rows:
            etype_value = _enum_value(etype)
            label = f"{etype_value}:{key}" if key is not None else etype_value
            out.setdefault(slug, {})[label] = out.setdefault(slug, {}).get(
                label, 0
            ) + int(count)
        return out

    async def cohorts(self, include_archived: bool) -> list[CohortMetaRow]:
        member_count = (
            select(func.count(func.distinct(CohortMembership.student_id)))
            .where(
                CohortMembership.cohort_id == Cohort.id,
                CohortMembership.status == CohortMembershipStatus.active,
            )
            .scalar_subquery()
        )
        assignment_count = (
            select(func.count())
            .where(Assignment.cohort_id == Cohort.id)
            .scalar_subquery()
        )
        stmt = select(
            Cohort.slug,
            Cohort.name,
            Cohort.academic_year,
            Cohort.archived,
            member_count.label("enrolled_count"),
            assignment_count.label("assignment_count"),
        )
        if not include_archived:
            stmt = stmt.where(Cohort.archived.is_(False))
        stmt = stmt.order_by(Cohort.created_at.desc())
        rows = await self._session.execute(stmt)
        return [
            CohortMetaRow(
                cohort_slug=row.slug,
                name=row.name,
                academic_year=row.academic_year,
                archived=bool(row.archived),
                enrolled_count=int(row.enrolled_count or 0),
                assignment_count=int(row.assignment_count or 0),
            )
            for row in rows
        ]


def _enum_value(value):
    return value.value if hasattr(value, "value") else value
