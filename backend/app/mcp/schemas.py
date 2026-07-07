from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AttemptFilters(BaseModel):
    cohort_slug: str | None = None
    case_slug: str | None = None
    status: Literal["in_progress", "completed", "abandoned"] | None = None
    started_after: date | None = None
    started_before: date | None = None
    language: Literal["en", "lv"] | None = None
    mode: str | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class AttemptSummary(BaseModel):
    attempt_ref: str
    student_pseudo: str | None
    case_slug: str
    cohort_slug: str | None
    assignment_ref: str | None
    language: str
    mode: str
    phase: str
    status: str
    started_on: date | None
    completed_on: date | None


class AttemptListResult(BaseModel):
    total: int
    suppressed: bool = False
    reason: str | None = None
    items: list[AttemptSummary] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    type: str
    seq: int
    offset_secs: int
    data: dict


class AttemptTimeline(BaseModel):
    attempt_ref: str
    student_pseudo: str | None
    case_slug: str
    cohort_slug: str | None
    suppressed: bool = False
    reason: str | None = None
    events: list[TimelineEvent] = Field(default_factory=list)


class FeedbackScores(BaseModel):
    historyTaking: str | None = None
    examination: str | None = None
    differential: str | None = None
    testSelection: str | None = None
    interpretation: str | None = None
    management: str | None = None


class AttemptFeedback(BaseModel):
    attempt_ref: str
    student_pseudo: str | None
    case_slug: str
    cohort_slug: str | None
    diagnosticAccuracy: str | None
    scores: FeedbackScores
    hints_used: int
    suppressed: bool = False
    reason: str | None = None


class CohortMeta(BaseModel):
    cohort_slug: str
    name: str
    academic_year: str | None
    archived: bool
    enrolled_band: str
    assignment_count: int


class CohortListResult(BaseModel):
    items: list[CohortMeta] = Field(default_factory=list)


class AggregateFilters(BaseModel):
    cohort_slug: str | None = None
    case_slug: str | None = None
    language: Literal["en", "lv"] | None = None
    mode: str | None = None
    metric: Literal[
        "completion_rate",
        "score_distribution",
        "attempts_per_case",
        "wrong_path_frequency",
        "clue_discovery_frequency",
        "hint_usage",
        "all",
    ] = "all"


class AggregateStats(BaseModel):
    completion_rate: dict | None = None
    score_distribution: dict | None = None
    attempts_per_case: dict | None = None
    wrong_path_frequency: dict | None = None
    clue_discovery_frequency: dict | None = None
    hint_usage: dict | None = None
    error: str | None = None
