from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.attempt import Attempt
from app.models.case import Case as CaseModel
from app.models.case import CaseVersion
from app.models.event import Event, EventType

SCORE_DIMENSIONS = (
    "historyTaking",
    "examination",
    "differential",
    "testSelection",
    "interpretation",
    "management",
)

SCORE_LEVELS = ("Excellent", "Good", "Developing", "Needs review")
ACCURACY_LEVELS = ("correct", "partially_correct", "incorrect")

FEEDBACK_GENERATED = EventType.FeedbackGenerated
DIFFERENTIALS_EVALUATED = EventType.DifferentialsEvaluated


@dataclass(frozen=True)
class FeedbackScoreRow:
    diagnostic_accuracy: str | None
    scores: dict[str, str | None]


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _cohort_attempts(self, cohort_id: uuid.UUID):
        return (
            select(Attempt.id)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .where(Assignment.cohort_id == cohort_id)
        )

    async def attempts_per_case(
        self, cohort_id: uuid.UUID
    ) -> dict[str, int]:
        stmt = (
            select(CaseModel.slug, func.count())
            .select_from(Attempt)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .where(Assignment.cohort_id == cohort_id)
            .group_by(CaseModel.slug)
        )
        rows = await self._session.execute(stmt)
        return {slug: int(count) for slug, count in rows}

    async def completed_per_case(
        self, cohort_id: uuid.UUID
    ) -> dict[str, int]:
        completed = (
            select(Event.attempt_id)
            .where(Event.type == FEEDBACK_GENERATED)
            .group_by(Event.attempt_id)
            .subquery()
        )
        stmt = (
            select(CaseModel.slug, func.count())
            .select_from(Attempt)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(CaseVersion, CaseVersion.id == Attempt.case_version_id)
            .join(CaseModel, CaseModel.id == CaseVersion.case_id)
            .join(completed, completed.c.attempt_id == Attempt.id)
            .where(Assignment.cohort_id == cohort_id)
            .group_by(CaseModel.slug)
        )
        rows = await self._session.execute(stmt)
        return {slug: int(count) for slug, count in rows}

    async def feedback_scores(
        self, cohort_id: uuid.UUID
    ) -> list[FeedbackScoreRow]:
        latest = (
            select(
                Event.attempt_id.label("attempt_id"),
                func.max(Event.seq).label("max_seq"),
            )
            .where(Event.type == FEEDBACK_GENERATED)
            .group_by(Event.attempt_id)
            .subquery()
        )
        fb_event = Event.__table__.alias("fb_event")
        scores = fb_event.c.data["feedback"]["scores"]
        accuracy = fb_event.c.data["feedback"]["diagnosticAccuracy"].astext
        columns = [accuracy.label("diagnostic_accuracy")]
        for dim in SCORE_DIMENSIONS:
            columns.append(scores[dim].astext.label(f"score_{dim}"))
        stmt = (
            select(*columns)
            .select_from(Attempt)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .join(latest, latest.c.attempt_id == Attempt.id)
            .join(
                fb_event,
                (fb_event.c.attempt_id == latest.c.attempt_id)
                & (fb_event.c.seq == latest.c.max_seq),
            )
            .where(Assignment.cohort_id == cohort_id)
        )
        rows = await self._session.execute(stmt)
        out: list[FeedbackScoreRow] = []
        for row in rows:
            mapping = row._mapping
            out.append(
                FeedbackScoreRow(
                    diagnostic_accuracy=row.diagnostic_accuracy,
                    scores={
                        dim: mapping[f"score_{dim}"]
                        for dim in SCORE_DIMENSIONS
                    },
                )
            )
        return out

    async def wrong_path_counts(
        self, cohort_id: uuid.UUID
    ) -> dict[str, int]:
        wrong_key = Event.data["wrong_key"].astext
        source = Event.data["source"].astext
        stmt = (
            select(wrong_key, func.count())
            .select_from(Event)
            .join(Attempt, Attempt.id == Event.attempt_id)
            .join(Assignment, Assignment.id == Attempt.assignment_id)
            .where(
                Assignment.cohort_id == cohort_id,
                Event.type == DIFFERENTIALS_EVALUATED,
                source == "wrong_path",
                wrong_key.isnot(None),
            )
            .group_by(wrong_key)
        )
        rows = await self._session.execute(stmt)
        return {key: int(count) for key, count in rows}
