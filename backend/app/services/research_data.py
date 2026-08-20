from __future__ import annotations

import statistics
import uuid
from datetime import date, datetime

from app.mcp.schemas import (
    AggregateFilters,
    AggregateStats,
    AttemptFeedback,
    AttemptFilters,
    AttemptListResult,
    AttemptSummary,
    AttemptTimeline,
    CohortListResult,
    CohortMeta,
    FeedbackScores,
    TimelineEvent,
)
from app.repositories.research_repo import (
    SCORE_DIMENSIONS,
    AttemptFilterSpec,
    AttemptRow,
    FeedbackRow,
    ResearchRepository,
)
from app.services.research_pseudonym import assert_pepper_distinct

TIMELINE_EVENT_CAP = 1000

SCORE_LEVELS = ("Excellent", "Good", "Developing", "Needs review")
ACCURACY_LEVELS = ("correct", "partially_correct", "incorrect")

TIMELINE_ALLOW_LIST: dict[str, tuple[str, ...]] = {
    "SessionStarted": ("mode", "language"),
    "SystemMessageAppended": (),
    "StudentMessageSent": (),
    "ScidNudgeFired": (),
    "PhaseChanged": ("from_phase", "to_phase"),
    "TestOrdered": ("key",),
    "LabResultShown": ("key", "is_genetic"),
    "GeneticNudgeShown": (),
    "TestUnavailableNoted": ("key", "channel"),
    "OrderBatchNoted": ("any_new", "channel"),
    "TestOrderUnrecognized": (),
    "ParentReplyRequested": (),
    "ParentReplyAppended": (),
    "ExamNudgeShown": (),
    "ExamPerformed": (),
    "ExamPathognomonicNoted": (),
    "SummarySet": (),
    "SummaryEvaluated": (),
    "DifferentialsSet": (),
    "DifferentialsEvaluated": ("source", "wrong_key"),
    "InterpTextSet": (),
    "InterpretationEvaluated": ("error",),
    "InterpretationReset": (),
    "FinalAnswerFieldSet": ("field_name",),
    "FinalAnswerSubmitted": (),
    "FeedbackGenerated": (),
    "HintRequested": (),
    "ReflectionAnswered": (),
    "ReflectionStepAdvanced": ("to_step",),
    "ReflectionSummarized": (),
    "ModeChanged": ("from_mode", "to_mode"),
    "TutorPromptAppended": ("channel",),
}

LOW_N = "low_n"


class ResearchDataService:
    def __init__(
        self,
        repo: ResearchRepository,
        pepper: str,
        pgcrypto_key: str,
        login_hash_pepper: str,
        k_anon_threshold: int,
    ) -> None:
        assert_pepper_distinct(pepper, pgcrypto_key, login_hash_pepper)
        self._repo = repo
        self._k = k_anon_threshold

    def _spec(self, filters) -> AttemptFilterSpec:
        return AttemptFilterSpec(
            cohort_slug=filters.cohort_slug,
            case_slug=filters.case_slug,
            language=getattr(filters, "language", None),
            mode=getattr(filters, "mode", None),
            started_after=_as_datetime(getattr(filters, "started_after", None)),
            started_before=_as_datetime(getattr(filters, "started_before", None)),
        )

    async def _group_size(self, spec: AttemptFilterSpec) -> int:
        if spec.cohort_slug is not None:
            count = await self._repo.cohort_student_count(spec.cohort_slug)
            if count is not None:
                return count
        return await self._repo.distinct_students_for_filter(spec)

    async def list_attempts(self, filters: AttemptFilters) -> AttemptListResult:
        spec = self._spec(filters)
        total = await self._repo.count_attempts(spec)
        group_size = await self._group_size(spec)
        if group_size < self._k:
            return AttemptListResult(total=total, suppressed=True, reason=LOW_N)
        rows = await self._repo.list_attempts(spec, filters.limit, filters.offset)
        items = [self._attempt_summary(row) for row in rows]
        if filters.status is not None:
            items = [item for item in items if item.status == filters.status]
        return AttemptListResult(total=total, items=items)

    def _attempt_summary(self, row: AttemptRow) -> AttemptSummary:
        return AttemptSummary(
            attempt_ref=str(row.attempt_id),
            student_pseudo=row.student_pseudo,
            case_slug=row.case_slug,
            cohort_slug=row.cohort_slug,
            assignment_ref=str(row.assignment_id) if row.assignment_id else None,
            language=row.language,
            mode=row.mode,
            phase=row.last_phase or "history",
            status=_status_of(row),
            started_on=_coarsen(row.started_at),
            completed_on=_coarsen(row.completed_at),
        )

    async def get_attempt_timeline(
        self, attempt_ref: str
    ) -> AttemptTimeline | None:
        attempt_id = _parse_uuid(attempt_ref)
        if attempt_id is None:
            return None
        header = await self._repo.attempt_header(attempt_id)
        if header is None:
            return None
        spec = AttemptFilterSpec(cohort_slug=header.cohort_slug)
        if header.student_pseudo is not None:
            group_size = await self._group_size(spec)
            if group_size < self._k:
                return AttemptTimeline(
                    attempt_ref=str(header.attempt_id),
                    student_pseudo=header.student_pseudo,
                    case_slug=header.case_slug,
                    cohort_slug=header.cohort_slug,
                    suppressed=True,
                    reason=LOW_N,
                )
        start = await self._repo.attempt_start(attempt_id)
        rows = await self._repo.timeline(attempt_id, TIMELINE_EVENT_CAP)
        events: list[TimelineEvent] = []
        for row in rows:
            events.append(
                TimelineEvent(
                    type=row.type,
                    seq=row.seq,
                    offset_secs=_offset_secs(start, row.created_at),
                    data=_scrub_timeline(row.type, row.data),
                )
            )
        return AttemptTimeline(
            attempt_ref=str(header.attempt_id),
            student_pseudo=header.student_pseudo,
            case_slug=header.case_slug,
            cohort_slug=header.cohort_slug,
            events=events,
        )

    async def get_feedback(self, attempt_ref: str) -> AttemptFeedback | None:
        attempt_id = _parse_uuid(attempt_ref)
        if attempt_id is None:
            return None
        header = await self._repo.attempt_header(attempt_id)
        if header is None:
            return None
        spec = AttemptFilterSpec(cohort_slug=header.cohort_slug)
        if header.student_pseudo is not None:
            group_size = await self._group_size(spec)
            if group_size < self._k:
                return AttemptFeedback(
                    attempt_ref=str(header.attempt_id),
                    student_pseudo=header.student_pseudo,
                    case_slug=header.case_slug,
                    cohort_slug=header.cohort_slug,
                    diagnosticAccuracy=None,
                    scores=FeedbackScores(),
                    hints_used=0,
                    suppressed=True,
                    reason=LOW_N,
                )
        rows = await self._repo.feedback_rows(
            AttemptFilterSpec(), attempt_id=attempt_id
        )
        if not rows:
            return None
        row = rows[0]
        return AttemptFeedback(
            attempt_ref=str(row.attempt_id),
            student_pseudo=row.student_pseudo,
            case_slug=row.case_slug,
            cohort_slug=row.cohort_slug,
            diagnosticAccuracy=row.diagnostic_accuracy,
            scores=_scores_dto(row),
            hints_used=row.hints_used,
        )

    async def list_cohorts(
        self, include_archived: bool = False
    ) -> CohortListResult:
        rows = await self._repo.cohorts(include_archived)
        return CohortListResult(
            items=[
                CohortMeta(
                    cohort_slug=row.cohort_slug,
                    name=row.name,
                    academic_year=row.academic_year,
                    archived=row.archived,
                    enrolled_band=_band(row.enrolled_count),
                    assignment_count=row.assignment_count,
                )
                for row in rows
            ]
        )

    async def aggregate_stats(self, filters: AggregateFilters) -> AggregateStats:
        if (
            filters.metric == "all"
            and filters.cohort_slug is None
            and filters.case_slug is None
        ):
            return AggregateStats(
                error="metric='all' requires cohort_slug or case_slug"
            )
        spec = self._spec(filters)
        metric = filters.metric
        out = AggregateStats()
        want = (
            {metric}
            if metric != "all"
            else {
                "completion_rate",
                "score_distribution",
                "attempts_per_case",
                "wrong_path_frequency",
                "clue_discovery_frequency",
                "hint_usage",
            }
        )
        if "completion_rate" in want:
            out.completion_rate = await self._completion_rate(spec)
        if "score_distribution" in want:
            out.score_distribution = await self._score_distribution(spec)
        if "attempts_per_case" in want:
            out.attempts_per_case = await self._attempts_per_case(spec)
        if "wrong_path_frequency" in want:
            out.wrong_path_frequency = await self._wrong_path_frequency(spec)
        if "clue_discovery_frequency" in want:
            out.clue_discovery_frequency = await self._clue_discovery(spec)
        if "hint_usage" in want:
            out.hint_usage = await self._hint_usage(spec)
        return out

    async def _completion_rate(self, spec: AttemptFilterSpec) -> dict:
        totals = await self._repo.attempts_per_case(spec)
        completed = await self._repo.completed_per_case(spec)
        by_case: dict[str, dict] = {}
        for slug, total in totals.items():
            done = completed.get(slug, 0)
            by_case[slug] = {
                "completed": _cell(done, self._k),
                "total": _cell(total, self._k),
                "rate": (round(done / total, 3) if total >= self._k else LOW_N),
            }
        return {"by_case": by_case}

    async def _score_distribution(self, spec: AttemptFilterSpec) -> dict:
        rows = await self._repo.feedback_rows(spec)
        by_dimension: dict[str, dict[str, int]] = {
            dim: dict.fromkeys(SCORE_LEVELS, 0) for dim in SCORE_DIMENSIONS
        }
        accuracy = dict.fromkeys(ACCURACY_LEVELS, 0)
        for row in rows:
            for dim in SCORE_DIMENSIONS:
                value = row.scores.get(dim)
                if value in by_dimension[dim]:
                    by_dimension[dim][value] += 1
            if row.diagnostic_accuracy in accuracy:
                accuracy[row.diagnostic_accuracy] += 1
        return {
            "by_dimension": {
                dim: {
                    level: _cell(count, self._k)
                    for level, count in levels.items()
                }
                for dim, levels in by_dimension.items()
            },
            "diagnostic_accuracy": {
                level: _cell(count, self._k)
                for level, count in accuracy.items()
            },
        }

    async def _attempts_per_case(self, spec: AttemptFilterSpec) -> dict:
        counts = await self._repo.attempts_per_case(spec)
        return {slug: _cell(count, self._k) for slug, count in counts.items()}

    async def _wrong_path_frequency(self, spec: AttemptFilterSpec) -> dict:
        rows = await self._repo.wrong_path_counts(spec)
        by_wrong_key: dict[str, int] = {}
        by_case: dict[str, dict[str, int]] = {}
        for slug, key, count in rows:
            by_wrong_key[key] = by_wrong_key.get(key, 0) + count
            by_case.setdefault(slug, {})[key] = (
                by_case.setdefault(slug, {}).get(key, 0) + count
            )
        return {
            "by_wrong_key": {
                key: _cell(count, self._k)
                for key, count in by_wrong_key.items()
            },
            "by_case": {
                slug: {
                    key: _cell(count, self._k) for key, count in keys.items()
                }
                for slug, keys in by_case.items()
            },
        }

    async def _clue_discovery(self, spec: AttemptFilterSpec) -> dict:
        counts = await self._repo.clue_event_counts(spec)
        return {
            "by_case": {
                slug: {
                    label: _cell(count, self._k)
                    for label, count in labels.items()
                }
                for slug, labels in counts.items()
            }
        }

    async def _hint_usage(self, spec: AttemptFilterSpec) -> dict:
        rows = await self._repo.hint_counts_per_attempt(spec)
        values = [count for _, count in rows]
        per_case: dict[str, list[int]] = {}
        for slug, count in rows:
            per_case.setdefault(slug, []).append(count)
        if len(values) < self._k:
            return {
                "mean": LOW_N,
                "median": LOW_N,
                "max": LOW_N,
                "by_case": {},
            }
        return {
            "mean": round(statistics.mean(values), 3),
            "median": statistics.median(values),
            "max": max(values),
            "by_case": {
                slug: (
                    round(statistics.mean(vals), 3)
                    if len(vals) >= self._k
                    else LOW_N
                )
                for slug, vals in per_case.items()
            },
        }


def _scrub_timeline(event_type: str, data: dict) -> dict:
    allowed = TIMELINE_ALLOW_LIST.get(event_type, ())
    if not data:
        return {}
    return {key: data[key] for key in allowed if key in data}


def _scores_dto(row: FeedbackRow) -> FeedbackScores:
    return FeedbackScores(
        historyTaking=row.scores.get("historyTaking"),
        examination=row.scores.get("examination"),
        differential=row.scores.get("differential"),
        testSelection=row.scores.get("testSelection"),
        interpretation=row.scores.get("interpretation"),
        management=row.scores.get("management"),
    )


def _status_of(row: AttemptRow) -> str:
    if row.has_feedback:
        return "completed"
    return "in_progress"


def _cell(count: int, k: int):
    return count if count >= k or count == 0 else LOW_N


def _band(count: int) -> str:
    if count < 5:
        return "<5"
    if count < 10:
        return "5-9"
    if count < 20:
        return "10-19"
    return "20+"


def _coarsen(value: datetime | None) -> date | None:
    if value is None:
        return None
    return value.date()


def _offset_secs(start: datetime | None, created_at: datetime | None) -> int:
    if start is None or created_at is None:
        return 0
    return int((created_at - start).total_seconds())


def _as_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return value


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None
