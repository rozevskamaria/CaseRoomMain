from __future__ import annotations

import itertools
import types
import uuid

import pytest

import app.api.runtime as runtime
from app.api.graphql.auth_guards import AuthError
from app.api.graphql.schema import Query
from app.models.case import (
    Case as CaseModel,
    CaseLocalizationEN,
    CaseVersion,
    CaseVersionStatus,
    Language,
)
from app.models.user import UserRole, UserStatus
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.case_repo import CaseRepository
from app.repositories.cohort_repo import CohortAccessError, CohortRepository
from app.repositories.user_repo import UserRepository
from app.services.cohort import CohortService
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration


MINIMAL_CONTENT = {
    "title": "Case",
    "patient": "Patient",
    "opening_clinical": "Vignette.",
    "opening": "Opening.",
    "red_flags": ["flag"],
    "parent_prompt": "Parent.",
    "lab_data": {"CBC": "WBC 12.0"},
    "exam_findings": "Findings.",
    "model_diagnosis": "Dx",
    "model_management": "Mgmt",
    "model_genetic_counselling": "Counselling",
    "key_clues": ["clue"],
    "wrong_paths": {"sepsis": "Reconsider."},
}


class FakeLLMClient:
    async def generate(self, system, messages, max_tokens):
        return "x"

    async def generate_structured(self, system, messages, schema, max_tokens):
        return {}

    async def stream(self, system, messages, max_tokens):
        yield "x"


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


def _info(user, db_session):
    context = types.SimpleNamespace(current_user=user, db_session=db_session)
    return types.SimpleNamespace(context=context)


async def _seed_case(session, slug: str, version_no: int = 1) -> CaseVersion:
    existing = await CaseRepository(session).get_case_version(slug)
    if existing is None:
        case = CaseModel(slug=slug)
        session.add(case)
        await session.flush()
        case_id = case.id
    else:
        case_id = existing.case_id
        case = await session.get(CaseModel, case_id)
    version = CaseVersion(
        case_id=case_id,
        version_no=version_no,
        status=CaseVersionStatus.published,
        difficulty="medium",
        target_diagnosis="Dx",
        topic="Topic",
        iuis="IUIS",
        created_by=None,
    )
    session.add(version)
    await session.flush()
    case.current_version_id = version.id
    session.add(
        CaseLocalizationEN(
            case_version_id=version.id,
            language=Language.en,
            content=MINIMAL_CONTENT,
        )
    )
    await session.flush()
    return version


def _services(db_session):
    cases = CaseRepository(db_session)
    session_service = SessionService(
        FakeLLMClient(),
        store=DbAttemptStore(AttemptRepository(db_session), cases),
        cases=DbCaseSource(cases),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )
    cohort_service = CohortService(
        CohortRepository(db_session), AssignmentRepository(db_session), cases
    )
    return session_service, cohort_service


async def test_create_assignment_pins_current_version(db_session):
    await _seed_case(db_session, "xla", version_no=1)
    version_two = await _seed_case(db_session, "xla", version_no=2)
    users = UserRepository(db_session)
    staff = await users.create_staff("aaaaaa", "a@rsu.edu.lv", "A", UserRole.staff)
    await users.set_status(staff.id, UserStatus.active)
    _, cohort_service = _services(db_session)
    cohort = await cohort_service.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    assignment = await cohort_service.create_assignment(
        cohort_id=str(cohort.id),
        case_id="xla",
        mode="practice",
        language="en",
        title=None,
        opens_at=None,
        due_at=None,
        created_by=str(staff.id),
    )
    assert assignment.case_version_id == version_two.id


async def test_create_assignment_rejects_unknown_case(db_session):
    users = UserRepository(db_session)
    staff = await users.create_staff("aaaaaa", "a@rsu.edu.lv", "A", UserRole.staff)
    await users.set_status(staff.id, UserStatus.active)
    _, cohort_service = _services(db_session)
    cohort = await cohort_service.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    with pytest.raises(CohortAccessError):
        await cohort_service.create_assignment(
            cohort_id=str(cohort.id),
            case_id="not-a-real-case",
            mode="practice",
            language="en",
            title=None,
            opens_at=None,
            due_at=None,
            created_by=str(staff.id),
        )


async def test_start_assignment_sets_assignment_id_free_play_null(db_session):
    await _seed_case(db_session, "xla")
    users = UserRepository(db_session)
    staff = await users.create_staff("aaaaaa", "a@rsu.edu.lv", "A", UserRole.staff)
    await users.set_status(staff.id, UserStatus.active)
    student = await users.create_student("100100", "S")
    await users.set_status(student.id, UserStatus.active)

    session_service, cohort_service = _services(db_session)
    cohort = await cohort_service.create_cohort(
        name="C", academic_year=None, created_by=str(staff.id)
    )
    await cohort_service.add_member(
        cohort_id=str(cohort.id), login_name="100100", actor_id=str(staff.id)
    )
    assignment = await cohort_service.create_assignment(
        cohort_id=str(cohort.id),
        case_id="xla",
        mode="practice",
        language="en",
        title=None,
        opens_at=None,
        due_at=None,
        created_by=str(staff.id),
    )
    assigned = await session_service.start_case(
        "xla", "practice", student_id=str(student.id),
        assignment_id=str(assignment.id),
    )
    free = await session_service.start_case(
        "xla", "practice", student_id=str(student.id)
    )
    repo = AttemptRepository(db_session)
    assigned_row = await repo.get_attempt(uuid.UUID(assigned.id))
    free_row = await repo.get_attempt(uuid.UUID(free.id))
    assert str(assigned_row.assignment_id) == str(assignment.id)
    assert free_row.assignment_id is None


async def test_list_for_student_only_own_cohorts(db_session):
    await _seed_case(db_session, "xla")
    users = UserRepository(db_session)
    staff = await users.create_staff("aaaaaa", "a@rsu.edu.lv", "A", UserRole.staff)
    await users.set_status(staff.id, UserStatus.active)
    student_a = await users.create_student("100100", "A")
    await users.set_status(student_a.id, UserStatus.active)
    student_b = await users.create_student("200200", "B")
    await users.set_status(student_b.id, UserStatus.active)

    _, cohort_service = _services(db_session)
    cohort_a = await cohort_service.create_cohort(
        name="A", academic_year=None, created_by=str(staff.id)
    )
    cohort_b = await cohort_service.create_cohort(
        name="B", academic_year=None, created_by=str(staff.id)
    )
    await cohort_service.add_member(
        cohort_id=str(cohort_a.id), login_name="100100", actor_id=str(staff.id)
    )
    await cohort_service.add_member(
        cohort_id=str(cohort_b.id), login_name="200200", actor_id=str(staff.id)
    )
    await cohort_service.create_assignment(
        cohort_id=str(cohort_a.id), case_id="xla", mode="practice",
        language="en", title=None, opens_at=None, due_at=None,
        created_by=str(staff.id),
    )

    repo = AssignmentRepository(db_session)
    for_a = await repo.list_for_student(student_a.id)
    for_b = await repo.list_for_student(student_b.id)
    assert len(for_a) == 1
    assert for_b == []


async def test_student_attempts_query_denies_non_member(db_session):
    await _seed_case(db_session, "xla")
    users = UserRepository(db_session)
    staff_a = await users.create_staff("aaaaaa", "a@rsu.edu.lv", "A", UserRole.staff)
    await users.set_status(staff_a.id, UserStatus.active)
    student_b = await users.create_student("200200", "B")
    await users.set_status(student_b.id, UserStatus.active)

    session_service, cohort_service = _services(db_session)
    cohort_a = await cohort_service.create_cohort(
        name="A", academic_year=None, created_by=str(staff_a.id)
    )

    svc_token = runtime.use_request_service(session_service)
    coh_token = runtime.use_request_cohort_service(cohort_service)
    try:
        query = Query()
        with pytest.raises(AuthError, match="Forbidden"):
            await query.student_attempts(
                _info(staff_a, db_session),
                cohort_id=str(cohort_a.id),
                student_id=str(student_b.id),
            )
    finally:
        runtime.reset_request_cohort_service(coh_token)
        runtime.reset_request_service(svc_token)
