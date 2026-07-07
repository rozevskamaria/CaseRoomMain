from __future__ import annotations

import json
import re
import uuid

import pytest

from app.mcp.schemas import AggregateFilters, AttemptFilters
from app.models.assignment import Assignment
from app.models.case import (
    Case as CaseModel,
)
from app.models.case import (
    CaseLocalizationEN,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.models.cohort import Cohort, CohortMembership, CohortMembershipStatus
from app.models.event import EventType as ModelEventType
from app.repositories.attempt_repo import AttemptRepository, NewEvent
from app.repositories.research_repo import ResearchRepository
from app.repositories.user_repo import UserRepository
from app.services.research_data import LOW_N, ResearchDataService

pytestmark = pytest.mark.dbintegration

PEPPER = "research-pepper-distinct-value"
PGCRYPTO = "test-pgcrypto-key-for-suite"
LOGIN_PEPPER = "test-login-hash-pepper-for-suite"

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

BANNED_KEYS = {
    "login_name",
    "login_name_hash",
    "email",
    "full_name",
    "user_id",
    "student_id",
    "id",
    "diagnosticComment",
    "wellDone",
    "missing",
    "keyClues",
    "reasoningPathway",
    "managementPoints",
    "geneticPoints",
    "revisionTopic",
    "text",
    "ans_text",
    "value",
}

CONTENT = {
    "title": "Test Case",
    "patient": "Test patient",
    "opening_clinical": "Opening clinical vignette.",
    "opening": "Opening line.",
    "red_flags": ["flag one"],
    "parent_prompt": "You are a worried parent.",
    "lab_data": {"CBC": "WBC 12.0\nHb 11.0"},
    "exam_findings": "Findings.",
    "model_diagnosis": "Test diagnosis",
    "model_management": "Test management",
    "model_genetic_counselling": "Test counselling",
    "key_clues": ["clue one"],
    "wrong_paths": {"sepsis": "Reconsider sepsis."},
}

FEEDBACK_BLOB = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "STUDENT SAID their name is Janis — leak vector",
    "wellDone": "You did great, Janis",
    "keyClues": ["clue one"],
    "scores": {
        "historyTaking": "Excellent",
        "examination": "Good",
        "differential": "Developing",
        "testSelection": "Good",
        "interpretation": "Needs review",
        "management": "Excellent",
    },
}


def _service(session) -> ResearchDataService:
    return ResearchDataService(
        ResearchRepository(session, PEPPER),
        PEPPER,
        PGCRYPTO,
        LOGIN_PEPPER,
        k_anon_threshold=5,
    )


async def _seed_case(session, slug: str) -> CaseVersion:
    case = CaseModel(slug=slug)
    session.add(case)
    await session.flush()
    version = CaseVersion(
        case_id=case.id,
        version_no=1,
        status=CaseVersionStatus.published,
        difficulty="medium",
        target_diagnosis="Test diagnosis",
        topic="Test topic",
        iuis="Test IUIS",
        created_by=None,
    )
    session.add(version)
    await session.flush()
    case.current_version_id = version.id
    session.add(
        CaseLocalizationEN(
            case_version_id=version.id, language=Language.en, content=CONTENT
        )
    )
    await session.flush()
    return version


async def _make_student(session, login: str):
    repo = UserRepository(session)
    return await repo.create_student(login, f"Student {login}")


async def _make_cohort(session, name: str) -> Cohort:
    cohort = Cohort(slug=f"{name}-{uuid.uuid4().hex[:8]}", name=name)
    session.add(cohort)
    await session.flush()
    return cohort


async def _enroll(session, cohort_id, student_id):
    session.add(
        CohortMembership(
            cohort_id=cohort_id,
            student_id=student_id,
            status=CohortMembershipStatus.active,
        )
    )
    await session.flush()


async def _make_assignment(session, cohort_id, version: CaseVersion) -> Assignment:
    assignment = Assignment(
        cohort_id=cohort_id,
        case_id=version.case_id,
        case_version_id=version.id,
        language=Language.en,
        mode="practice",
    )
    session.add(assignment)
    await session.flush()
    return assignment


async def _make_attempt(
    session, version, student_id, assignment_id, events: list[NewEvent]
):
    repo = AttemptRepository(session)
    attempt = await repo.create_attempt(
        case_version_id=version.id,
        mode="practice",
        language="en",
        student_id=student_id,
        assignment_id=assignment_id,
    )
    seeded = [
        NewEvent(
            type=ModelEventType.SessionStarted,
            data={"id": str(attempt.id), "case_slug": "x", "mode": "practice"},
        ),
        *events,
    ]
    await repo.append_events(attempt.id, seeded)
    return attempt


def _completed_events(accuracy="correct", scores=None) -> list[NewEvent]:
    blob = dict(FEEDBACK_BLOB)
    blob["diagnosticAccuracy"] = accuracy
    if scores is not None:
        blob = {**blob, "scores": scores}
    return [
        NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"}),
        NewEvent(
            type=ModelEventType.LabResultShown,
            data={
                "message_id": "m1",
                "text": "WBC 12 free text",
                "key": "CBC",
                "is_genetic": False,
            },
        ),
        NewEvent(type=ModelEventType.HintRequested, data={"hint_text": "secret hint"}),
        NewEvent(
            type=ModelEventType.DifferentialsEvaluated,
            data={
                "message_id": "m2",
                "text": "free text leak",
                "source": "wrong_path",
                "wrong_key": "sepsis",
            },
        ),
        NewEvent(
            type=ModelEventType.FeedbackGenerated,
            data={"feedback": blob},
        ),
        NewEvent(
            type=ModelEventType.PhaseChanged,
            data={"from_phase": "final", "to_phase": "feedback"},
        ),
    ]


async def _seed_cohort_of(session, n_students, version, completed=None):
    cohort = await _make_cohort(session, f"cohort{n_students}")
    assignment = await _make_assignment(session, cohort.id, version)
    students = []
    attempts = []
    for i in range(n_students):
        student = await _make_student(session, f"{n_students}{i:04d}"[:6].zfill(6))
        await _enroll(session, cohort.id, student.id)
        students.append(student)
        is_done = completed is None or i < completed
        events = _completed_events() if is_done else [
            NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"})
        ]
        attempt = await _make_attempt(
            session, version, student.id, assignment.id, events
        )
        attempts.append(attempt)
    return cohort, assignment, students, attempts


async def test_pseudonym_sql_matches_python(db_session):
    from app.services.research_pseudonym import research_pseudonym

    version = await _seed_case(db_session, "psqlcase")
    cohort, assignment, students, attempts = await _seed_cohort_of(
        db_session, 5, version
    )
    repo = ResearchRepository(db_session, PEPPER)
    header = await repo.attempt_header(attempts[0].id)
    expected = research_pseudonym(students[0].id, PEPPER)
    assert header.student_pseudo == expected


async def test_small_cohort_student_rows_suppressed(db_session):
    version = await _seed_case(db_session, "smallcohort")
    cohort, _, students, _ = await _seed_cohort_of(db_session, 3, version)
    service = _service(db_session)
    result = await service.list_attempts(
        AttemptFilters(cohort_slug=cohort.slug)
    )
    assert result.suppressed is True
    assert result.reason == LOW_N
    assert result.items == []
    blob = json.dumps(result.model_dump(mode="json"))
    for student in students:
        assert str(student.id) not in blob


async def test_large_cohort_student_rows_returned_pseudonymized(db_session):
    version = await _seed_case(db_session, "bigcohort")
    cohort, _, students, _ = await _seed_cohort_of(db_session, 5, version)
    service = _service(db_session)
    result = await service.list_attempts(
        AttemptFilters(cohort_slug=cohort.slug)
    )
    assert result.suppressed is False
    assert len(result.items) == 5
    student_ids = {str(s.id) for s in students}
    for item in result.items:
        assert item.student_pseudo is not None
        assert len(item.student_pseudo) == 64
        assert item.student_pseudo not in student_ids


async def test_timestamps_coarsened_to_date(db_session):
    version = await _seed_case(db_session, "datescase")
    cohort, _, _, _ = await _seed_cohort_of(db_session, 5, version)
    service = _service(db_session)
    result = await service.list_attempts(AttemptFilters(cohort_slug=cohort.slug))
    blob = result.model_dump(mode="json")
    for item in blob["items"]:
        assert "T" not in str(item["started_on"])
        if item["completed_on"] is not None:
            assert "T" not in str(item["completed_on"])


async def test_enrolled_count_banded(db_session):
    version = await _seed_case(db_session, "bandcase")
    cohort, _, _, _ = await _seed_cohort_of(db_session, 5, version)
    service = _service(db_session)
    result = await service.list_cohorts()
    meta = next(m for m in result.items if m.cohort_slug == cohort.slug)
    assert meta.enrolled_band in {"<5", "5-9", "10-19", "20+"}
    assert meta.enrolled_band == "5-9"
    blob = json.dumps(result.model_dump(mode="json"))
    assert "enrolled_count" not in blob


async def test_no_pii_in_any_tool_output(db_session):
    version = await _seed_case(db_session, "piicase")
    cohort, assignment, students, attempts = await _seed_cohort_of(
        db_session, 5, version
    )
    service = _service(db_session)
    outputs = []
    outputs.append(
        (await service.list_attempts(AttemptFilters(cohort_slug=cohort.slug))).model_dump(mode="json")
    )
    outputs.append(
        (await service.get_attempt_timeline(str(attempts[0].id))).model_dump(mode="json")
    )
    outputs.append(
        (await service.get_feedback(str(attempts[0].id))).model_dump(mode="json")
    )
    outputs.append((await service.list_cohorts()).model_dump(mode="json"))
    outputs.append(
        (
            await service.aggregate_stats(
                AggregateFilters(cohort_slug=cohort.slug, metric="all")
            )
        ).model_dump(mode="json")
    )
    student_ids = {str(s.id) for s in students}
    for output in outputs:
        _assert_no_banned_keys(output)
        blob = json.dumps(output)
        for sid in student_ids:
            assert sid not in blob
        assert "@rsu.edu.lv" not in blob
        assert "diagnosticComment" not in blob
        assert "Janis" not in blob
        for uuid_hit in UUID_RE.findall(blob):
            assert _is_allowed_uuid(uuid_hit, output)


def _is_allowed_uuid(value: str, output) -> bool:
    allowed = set()
    _collect_allowed_uuids(output, allowed)
    return value in allowed


def _collect_allowed_uuids(node, acc):
    if isinstance(node, dict):
        for key, val in node.items():
            if key in {"attempt_ref", "assignment_ref"} and isinstance(val, str):
                acc.add(val)
            else:
                _collect_allowed_uuids(val, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_allowed_uuids(item, acc)


def _assert_no_banned_keys(node):
    if isinstance(node, dict):
        for key, val in node.items():
            assert key not in BANNED_KEYS, f"banned key {key} in output"
            _assert_no_banned_keys(val)
    elif isinstance(node, list):
        for item in node:
            _assert_no_banned_keys(item)


async def test_timeline_scrubbed_no_free_text(db_session):
    version = await _seed_case(db_session, "tlcase")
    cohort, assignment, students, attempts = await _seed_cohort_of(
        db_session, 5, version
    )
    service = _service(db_session)
    timeline = await service.get_attempt_timeline(str(attempts[0].id))
    blob = json.dumps(timeline.model_dump(mode="json"))
    assert "WBC 12 free text" not in blob
    assert "free text leak" not in blob
    assert "secret hint" not in blob
    for event in timeline.events:
        if event.type == "DifferentialsEvaluated":
            assert event.data == {"source": "wrong_path", "wrong_key": "sepsis"}
        if event.type == "LabResultShown":
            assert event.data == {"key": "CBC", "is_genetic": False}


async def test_feedback_categorical_only_no_free_text(db_session):
    version = await _seed_case(db_session, "fbcase")
    cohort, assignment, students, attempts = await _seed_cohort_of(
        db_session, 5, version
    )
    service = _service(db_session)
    feedback = await service.get_feedback(str(attempts[0].id))
    assert feedback.diagnosticAccuracy == "correct"
    assert feedback.scores.historyTaking == "Excellent"
    assert feedback.hints_used == 1
    blob = json.dumps(feedback.model_dump(mode="json"))
    assert "diagnosticComment" not in blob
    assert "wellDone" not in blob
    assert "Janis" not in blob


async def test_aggregate_small_cell_low_n(db_session):
    version = await _seed_case(db_session, "aggsmall")
    cohort, _, _, _ = await _seed_cohort_of(db_session, 5, version, completed=2)
    service = _service(db_session)
    stats = await service.aggregate_stats(
        AggregateFilters(cohort_slug=cohort.slug, metric="score_distribution")
    )
    dist = stats.score_distribution
    history = dist["by_dimension"]["historyTaking"]
    assert history["Excellent"] == LOW_N
    assert history["Good"] == 0


async def test_aggregate_completion_and_attempts(db_session):
    version = await _seed_case(db_session, "aggcomplete")
    cohort, _, _, _ = await _seed_cohort_of(db_session, 6, version, completed=6)
    service = _service(db_session)
    stats = await service.aggregate_stats(
        AggregateFilters(cohort_slug=cohort.slug, metric="all")
    )
    assert stats.attempts_per_case["aggcomplete"] == 6
    by_case = stats.completion_rate["by_case"]["aggcomplete"]
    assert by_case["completed"] == 6
    assert by_case["total"] == 6
    assert by_case["rate"] == 1.0
    assert stats.wrong_path_frequency["by_wrong_key"]["sepsis"] == 6
    assert stats.hint_usage["mean"] == 1.0
    assert stats.hint_usage["max"] == 1


async def test_aggregate_metric_all_requires_filter(db_session):
    service = _service(db_session)
    stats = await service.aggregate_stats(AggregateFilters(metric="all"))
    assert stats.error is not None
    assert stats.completion_rate is None


async def test_fail_closed_pepper(db_session):
    from app.services.research_pseudonym import ResearchPseudonymError

    with pytest.raises(ResearchPseudonymError):
        ResearchDataService(
            ResearchRepository(db_session, ""),
            "",
            PGCRYPTO,
            LOGIN_PEPPER,
            k_anon_threshold=5,
        )


async def test_pepper_must_differ_from_pgcrypto(db_session):
    from app.services.research_pseudonym import ResearchPseudonymError

    with pytest.raises(ResearchPseudonymError):
        ResearchDataService(
            ResearchRepository(db_session, PGCRYPTO),
            PGCRYPTO,
            PGCRYPTO,
            LOGIN_PEPPER,
            k_anon_threshold=5,
        )
