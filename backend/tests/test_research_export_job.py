from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pytest

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
from app.repositories.user_repo import UserRepository
from app.workers.jobs import generate_research_export

pytestmark = pytest.mark.dbintegration

PEPPER = "research-pepper-distinct-value"
PGCRYPTO = "test-pgcrypto-key-for-suite"
LOGIN_PEPPER = "test-login-hash-pepper-for-suite"

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

CONTENT = {
    "title": "Test Case",
    "patient": "Test patient",
    "opening_clinical": "Opening clinical vignette.",
    "opening": "Opening line.",
    "red_flags": ["flag one"],
    "parent_prompt": "You are a worried parent.",
    "lab_data": {"CBC": "WBC 12.0"},
    "exam_findings": "Findings.",
    "model_diagnosis": "Test diagnosis",
    "model_management": "Test management",
    "model_genetic_counselling": "Test counselling",
    "key_clues": ["clue one"],
    "wrong_paths": {"sepsis": "Reconsider sepsis."},
}

FEEDBACK_BLOB = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "STUDENT named Janis Berzins — leak vector",
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


class _SessionmakerStub:
    def __init__(self, session):
        self._session = session

    def __call__(self):
        return self

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *exc):
        return None


def _ctx(session, tmp_path):
    from app.core.config import Settings

    settings = Settings(
        RESEARCH_PSEUDONYM_PEPPER=PEPPER,
        PGCRYPTO_KEY=PGCRYPTO,
        LOGIN_HASH_PEPPER=LOGIN_PEPPER,
        K_ANON_THRESHOLD=5,
        RESEARCH_EXPORT_DIR=str(tmp_path),
    )
    return {"sessionmaker": _SessionmakerStub(session), "settings": settings}


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


async def _make_cohort(session, name: str) -> Cohort:
    cohort = Cohort(slug=f"{name}-{uuid.uuid4().hex[:8]}", name=name)
    session.add(cohort)
    await session.flush()
    return cohort


async def _make_assignment(session, cohort_id, version) -> Assignment:
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


def _completed_events():
    return [
        NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"}),
        NewEvent(type=ModelEventType.HintRequested, data={"hint_text": "secret"}),
        NewEvent(
            type=ModelEventType.DifferentialsEvaluated,
            data={
                "text": "free text leak",
                "source": "wrong_path",
                "wrong_key": "sepsis",
            },
        ),
        NewEvent(
            type=ModelEventType.FeedbackGenerated, data={"feedback": FEEDBACK_BLOB}
        ),
        NewEvent(
            type=ModelEventType.PhaseChanged,
            data={"from_phase": "final", "to_phase": "feedback"},
        ),
    ]


async def _seed_cohort(session, n, version):
    cohort = await _make_cohort(session, "exportcohort")
    assignment = await _make_assignment(session, cohort.id, version)
    students = []
    repo = AttemptRepository(session)
    users = UserRepository(session)
    for i in range(n):
        student = await users.create_student(f"5{i:05d}"[:6], f"Janis {i}")
        session.add(
            CohortMembership(
                cohort_id=cohort.id,
                student_id=student.id,
                status=CohortMembershipStatus.active,
            )
        )
        await session.flush()
        students.append(student)
        attempt = await repo.create_attempt(
            case_version_id=version.id,
            mode="practice",
            language="en",
            student_id=student.id,
            assignment_id=assignment.id,
        )
        await repo.append_events(
            attempt.id,
            [
                NewEvent(
                    type=ModelEventType.SessionStarted,
                    data={"id": str(attempt.id), "mode": "practice"},
                ),
                *_completed_events(),
            ],
        )
    return cohort, students


async def test_export_job_produces_pseudonymized_files_no_pii(db_session, tmp_path):
    version = await _seed_case(db_session, "exportcase")
    cohort, students = await _seed_cohort(db_session, 5, version)

    result = await generate_research_export(
        _ctx(db_session, tmp_path), filters={"cohort_slug": cohort.slug}
    )

    assert result["attempt_count"] == 5
    assert result["suppressed"] is False
    json_path = Path(result["json_path"])
    csv_path = Path(result["csv_path"])
    assert json_path.exists()
    assert csv_path.exists()

    blob = json_path.read_text() + csv_path.read_text()

    for student in students:
        assert str(student.id) not in blob
    assert "@rsu.edu.lv" not in blob
    assert "Janis" not in blob
    assert "diagnosticComment" not in blob
    assert "wellDone" not in blob
    assert "free text leak" not in blob
    assert "secret" not in blob

    data = json.loads(json_path.read_text())
    pseudos = {item["student_pseudo"] for item in data["attempts"]["items"]}
    assert len(pseudos) == 5
    for pseudo in pseudos:
        assert len(pseudo) == 64

    student_ids = {str(s.id) for s in students}
    for uuid_hit in UUID_RE.findall(blob):
        assert uuid_hit not in student_ids


async def test_export_job_small_cohort_suppressed_no_rows(db_session, tmp_path):
    version = await _seed_case(db_session, "smallexport")
    cohort, students = await _seed_cohort(db_session, 3, version)

    result = await generate_research_export(
        _ctx(db_session, tmp_path), filters={"cohort_slug": cohort.slug}
    )
    assert result["suppressed"] is True
    data = json.loads(Path(result["json_path"]).read_text())
    assert data["attempts"]["items"] == []
    blob = Path(result["json_path"]).read_text()
    for student in students:
        assert str(student.id) not in blob
