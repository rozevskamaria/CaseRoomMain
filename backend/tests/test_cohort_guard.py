from __future__ import annotations

import itertools
import types
import uuid

import pytest

import app.api.runtime as runtime
from app.api.graphql.auth_guards import (
    AuthError,
    require_attempt_access,
    require_cohort_access,
)
from app.api.graphql.schema import AttemptType
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
from app.repositories.cohort_repo import CohortRepository
from app.repositories.user_repo import UserRepository
from app.services.cohort import CohortService
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration


MINIMAL_CONTENT = {
    "title": "Guard Case",
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


async def _seed_case(session, slug: str) -> CaseVersion:
    case = CaseModel(slug=slug)
    session.add(case)
    await session.flush()
    version = CaseVersion(
        case_id=case.id,
        version_no=1,
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


class Harness:
    def __init__(self, db_session):
        self.db = db_session
        self.users = UserRepository(db_session)
        self.cohorts = CohortRepository(db_session)
        self.assignments = AssignmentRepository(db_session)
        self.cases = CaseRepository(db_session)
        self.session_service = SessionService(
            FakeLLMClient(),
            store=DbAttemptStore(AttemptRepository(db_session), self.cases),
            cases=DbCaseSource(self.cases),
            rng=lambda: 0.0,
            id_factory=_ids(),
        )
        self.cohort_service = CohortService(
            self.cohorts, self.assignments, self.cases
        )

    async def __aenter__(self):
        self._svc_token = runtime.use_request_service(self.session_service)
        self._coh_token = runtime.use_request_cohort_service(self.cohort_service)
        return self

    async def __aexit__(self, *exc):
        runtime.reset_request_cohort_service(self._coh_token)
        runtime.reset_request_service(self._svc_token)

    async def make_student(self, login: str):
        user = await self.users.create_student(login, login)
        await self.users.set_status(user.id, UserStatus.active)
        return user

    async def make_staff(self, login: str, role=UserRole.staff):
        user = await self.users.create_staff(
            login, f"{login}@rsu.edu.lv", login, role
        )
        await self.users.set_status(user.id, UserStatus.active)
        return user

    async def create_cohort(self, name: str, creator) -> uuid.UUID:
        cohort = await self.cohort_service.create_cohort(
            name=name, academic_year="2025/2026", created_by=str(creator.id)
        )
        return cohort.id

    async def create_assignment(self, cohort_id, slug: str, creator):
        return await self.cohort_service.create_assignment(
            cohort_id=str(cohort_id),
            case_id=slug,
            mode="practice",
            language="en",
            title=None,
            opens_at=None,
            due_at=None,
            created_by=str(creator.id),
        )

    async def start_assigned_attempt(self, slug, student, assignment) -> str:
        proj = await self.session_service.start_case(
            slug,
            "practice",
            student_id=str(student.id),
            assignment_id=str(assignment.id),
        )
        return proj.id

    async def start_free_play(self, slug, student) -> str:
        proj = await self.session_service.start_case(
            slug, "practice", student_id=str(student.id)
        )
        return proj.id


async def test_staff_reads_attempt_on_their_cohort_assignment(db_session):
    version = await _seed_case(db_session, "xla")
    del version
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        student_a = await h.make_student("100100")
        cohort_a = await h.create_cohort("Cohort A", staff_a)
        await h.cohorts.add_member(
            cohort_id=cohort_a, login_name="100100", actor_id=staff_a.id
        )
        assignment = await h.create_assignment(cohort_a, "xla", staff_a)
        attempt_id = await h.start_assigned_attempt("xla", student_a, assignment)

        await require_attempt_access(
            _info(staff_a, db_session), attempt_id, write=False
        )


async def test_staff_denied_attempt_on_different_cohort_assignment(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        student_b = await h.make_student("200200")
        cohort_a = await h.create_cohort("Cohort A", staff_a)
        cohort_b = await h.create_cohort("Cohort B", staff_b)
        del cohort_a
        await h.cohorts.add_member(
            cohort_id=cohort_b, login_name="200200", actor_id=staff_b.id
        )
        assignment_b = await h.create_assignment(cohort_b, "xla", staff_b)
        attempt_id = await h.start_assigned_attempt("xla", student_b, assignment_b)

        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(staff_a, db_session), attempt_id, write=False
            )


async def test_enroll_to_read_is_dead(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        victim = await h.make_student("100100")

        cohort_a = await h.create_cohort("Cohort A", staff_a)
        cohort_b = await h.create_cohort("Cohort B", staff_b)

        free_play_id = await h.start_free_play("xla", victim)

        await h.cohorts.add_member(
            cohort_id=cohort_b, login_name="100100", actor_id=staff_b.id
        )
        assignment_b = await h.create_assignment(cohort_b, "xla", staff_b)
        cohort_b_attempt_id = await h.start_assigned_attempt(
            "xla", victim, assignment_b
        )

        await h.cohorts.add_member(
            cohort_id=cohort_a, login_name="100100", actor_id=staff_a.id
        )

        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(staff_a, db_session), free_play_id, write=False
            )
        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(staff_a, db_session), cohort_b_attempt_id, write=False
            )


async def test_staff_write_denied_on_own_cohort_attempt(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        student_a = await h.make_student("100100")
        cohort_a = await h.create_cohort("Cohort A", staff_a)
        await h.cohorts.add_member(
            cohort_id=cohort_a, login_name="100100", actor_id=staff_a.id
        )
        assignment = await h.create_assignment(cohort_a, "xla", staff_a)
        attempt_id = await h.start_assigned_attempt("xla", student_a, assignment)

        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(staff_a, db_session), attempt_id, write=True
            )


async def test_admin_reads_all_attempts(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        admin = await h.make_staff("admin1", role=UserRole.admin)
        student = await h.make_student("100100")
        free_play_id = await h.start_free_play("xla", student)
        anon_proj = await h.session_service.start_case("xla", "practice")

        await require_attempt_access(
            _info(admin, db_session), free_play_id, write=False
        )
        await require_attempt_access(
            _info(admin, db_session), anon_proj.id, write=False
        )


async def test_student_reads_own_including_free_play(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        student = await h.make_student("100100")
        other = await h.make_student("200200")
        free_play_id = await h.start_free_play("xla", student)

        await require_attempt_access(
            _info(student, db_session), free_play_id, write=False
        )
        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(other, db_session), free_play_id, write=False
            )


async def test_staff_denied_anonymous_attempt(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        await h.create_cohort("Cohort A", staff_a)
        anon_proj = await h.session_service.start_case("xla", "practice")

        with pytest.raises(AuthError, match="Forbidden"):
            await require_attempt_access(
                _info(staff_a, db_session), anon_proj.id, write=False
            )


async def test_nested_events_reasserts_guard(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        student_b = await h.make_student("200200")
        cohort_b = await h.create_cohort("Cohort B", staff_b)
        await h.cohorts.add_member(
            cohort_id=cohort_b, login_name="200200", actor_id=staff_b.id
        )
        assignment_b = await h.create_assignment(cohort_b, "xla", staff_b)
        attempt_id = await h.start_assigned_attempt("xla", student_b, assignment_b)

        attempt_type = AttemptType(
            id=attempt_id,
            case_id="xla",
            mode="practice",
            phase="history",
            status="in_progress",
            started_at=None,
            completed_at=None,
        )
        with pytest.raises(AuthError, match="Forbidden"):
            await attempt_type.events(_info(staff_a, db_session))


async def test_removed_membership_does_not_change_assignment_scope(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        student_a = await h.make_student("100100")
        cohort_a = await h.create_cohort("Cohort A", staff_a)
        await h.cohorts.add_member(
            cohort_id=cohort_a, login_name="100100", actor_id=staff_a.id
        )
        assignment = await h.create_assignment(cohort_a, "xla", staff_a)
        attempt_id = await h.start_assigned_attempt("xla", student_a, assignment)

        await h.cohorts.remove_member(
            cohort_id=cohort_a, student_id=student_a.id, actor_id=staff_a.id
        )

        await require_attempt_access(
            _info(staff_a, db_session), attempt_id, write=False
        )


async def test_cohort_access_scoping(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        admin = await h.make_staff("admin1", role=UserRole.admin)
        cohort_b = await h.create_cohort("Cohort B", staff_b)

        await require_cohort_access(
            _info(staff_b, db_session), str(cohort_b), write=False
        )
        await require_cohort_access(
            _info(admin, db_session), str(cohort_b), write=False
        )
        with pytest.raises(AuthError, match="Forbidden"):
            await require_cohort_access(
                _info(staff_a, db_session), str(cohort_b), write=False
            )
