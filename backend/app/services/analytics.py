from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.repositories.analytics_repo import (
    ACCURACY_LEVELS,
    SCORE_DIMENSIONS,
    SCORE_LEVELS,
    AnalyticsRepository,
)


@dataclass
class CohortAnalytics:
    cohort_id: str
    total_attempts: int
    completed_attempts: int
    completion_rate: float
    attempts_per_case: dict[str, int] = field(default_factory=dict)
    score_distribution: dict[str, dict[str, int]] = field(default_factory=dict)
    diagnostic_accuracy_distribution: dict[str, int] = field(
        default_factory=dict
    )
    wrong_path_frequency: dict[str, int] = field(default_factory=dict)


def _as_uuid(value: uuid.UUID | str) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)


class AnalyticsService:
    def __init__(self, repo: AnalyticsRepository) -> None:
        self._repo = repo

    async def cohort_analytics(self, cohort_id: str) -> CohortAnalytics:
        cid = _as_uuid(cohort_id)
        per_case = await self._repo.attempts_per_case(cid)
        completed_per_case = await self._repo.completed_per_case(cid)
        feedback = await self._repo.feedback_scores(cid)
        wrong_paths = await self._repo.wrong_path_counts(cid)

        total = sum(per_case.values())
        completed = sum(completed_per_case.values())
        rate = round(completed / total, 3) if total else 0.0

        distribution: dict[str, dict[str, int]] = {
            dim: dict.fromkeys(SCORE_LEVELS, 0) for dim in SCORE_DIMENSIONS
        }
        accuracy = dict.fromkeys(ACCURACY_LEVELS, 0)
        for row in feedback:
            for dim in SCORE_DIMENSIONS:
                value = row.scores.get(dim)
                if value in distribution[dim]:
                    distribution[dim][value] += 1
            if row.diagnostic_accuracy in accuracy:
                accuracy[row.diagnostic_accuracy] += 1

        return CohortAnalytics(
            cohort_id=str(cohort_id),
            total_attempts=total,
            completed_attempts=completed,
            completion_rate=rate,
            attempts_per_case=dict(per_case),
            score_distribution=distribution,
            diagnostic_accuracy_distribution=accuracy,
            wrong_path_frequency=dict(wrong_paths),
        )
