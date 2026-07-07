from __future__ import annotations

import itertools
import types

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
from app.models.event import EventType as ModelEventType
from app.models.user import UserRole, UserStatus
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.assignment_repo import AssignmentRepository
from app.repositories.attempt_repo import AttemptRepository, NewEvent
from app.repositories.case_repo import CaseRepository
from app.repositories.cohort_repo import CohortRepository
from app.repositories.user_repo import UserRepository
from app.services.analytics import AnalyticsService
from app.services.cohort import CohortService
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration

MINIMAL_CONTENT = {
    "title": "Analytics Case",
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

FEEDBACK_BLOB = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "leak",
    "scores": {
        "historyTaking": "Excellent",
        "examination": "Good",
        "differential": "Developing",
        "testSelection": "Good",
        "interpretation": "Needs review",
        "management": "Excellent",
    },
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
        self.attempts = AttemptRepository(db_session)
        self.session_service = SessionService(
            FakeLLMClient(),
            store=DbAttemptStore(self.attempts, self.cases),
            cases=DbCaseSource(self.cases),
            rng=lambda: 0.0,
            id_factory=_ids(),
        )
        self.cohort_service = CohortService(
            self.cohorts, self.assignments, self.cases
        )
        self.analytics_service = AnalyticsService(
            AnalyticsRepository(db_session)
        )

    async def __aenter__(self):
        self._svc = runtime.use_request_service(self.session_service)
        self._coh = runtime.use_request_cohort_service(self.cohort_service)
        self._an = runtime.use_request_analytics_service(self.analytics_service)
        return self

    async def __aexit__(self, *exc):
        runtime.reset_request_analytics_service(self._an)
        runtime.reset_request_cohort_service(self._coh)
        runtime.reset_request_service(self._svc)

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

    async def create_cohort(self, name: str, creator):
        cohort = await self.cohort_service.create_cohort(
            name=name, academic_year="2025/2026", created_by=str(creator.id)
        )
        return cohort

    async def create_assignment(self, cohort_id, slug, creator):
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

    async def attempt(self, slug, student, assignment, *, completed: bool):
        proj = await self.session_service.start_case(
            slug,
            "practice",
            student_id=str(student.id),
            assignment_id=str(assignment.id),
        )
        import uuid as _uuid

        attempt_id = _uuid.UUID(proj.id)
        events = [NewEvent(type=ModelEventType.TestOrdered, data={"key": "CBC"})]
        if completed:
            events += [
                NewEvent(
                    type=ModelEventType.DifferentialsEvaluated,
                    data={"source": "wrong_path", "wrong_key": "sepsis"},
                ),
                NewEvent(
                    type=ModelEventType.FeedbackGenerated,
                    data={"feedback": FEEDBACK_BLOB},
                ),
                NewEvent(
                    type=ModelEventType.PhaseChanged,
                    data={"from_phase": "final", "to_phase": "feedback"},
                ),
            ]
        await self.attempts.append_events(attempt_id, events)
        return proj.id


async def test_cohort_analytics_aggregates(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff = await h.make_staff("aaaaaa")
        cohort = await h.create_cohort("Cohort A", staff)
        assignment = await h.create_assignment(cohort.id, "xla", staff)
        for i in range(4):
            login = f"1001{i:02d}"
            student = await h.make_student(login)
            await h.cohorts.add_member(
                cohort_id=cohort.id, login_name=login, actor_id=staff.id
            )
            await h.attempt("xla", student, assignment, completed=(i < 3))

        result = await Query.cohort_analytics(
            Query(), _info(staff, db_session), str(cohort.id)
        )

    assert result.total_attempts == 4
    assert result.completed_attempts == 3
    assert result.completion_rate == 0.75
    assert result.attempts_per_case["xla"] == 4
    assert result.score_distribution["historyTaking"]["Excellent"] == 3
    assert result.score_distribution["interpretation"]["Needs review"] == 3
    assert result.diagnostic_accuracy_distribution["correct"] == 3
    assert result.wrong_path_frequency["sepsis"] == 3


async def test_cohort_analytics_admin_any_cohort(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff = await h.make_staff("aaaaaa")
        admin = await h.make_staff("admin1", role=UserRole.admin)
        cohort = await h.create_cohort("Cohort A", staff)
        assignment = await h.create_assignment(cohort.id, "xla", staff)
        student = await h.make_student("100100")
        await h.cohorts.add_member(
            cohort_id=cohort.id, login_name="100100", actor_id=staff.id
        )
        await h.attempt("xla", student, assignment, completed=True)

        result = await Query.cohort_analytics(
            Query(), _info(admin, db_session), str(cohort.id)
        )
    assert result.total_attempts == 1
    assert result.completed_attempts == 1


async def test_cohort_analytics_staff_denied_foreign_cohort(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        cohort_b = await h.create_cohort("Cohort B", staff_b)

        with pytest.raises(AuthError, match="Forbidden"):
            await Query.cohort_analytics(
                Query(), _info(staff_a, db_session), str(cohort_b.id)
            )


async def test_cohort_analytics_scoped_to_assignment_attempts(db_session):
    await _seed_case(db_session, "xla")
    async with Harness(db_session) as h:
        staff_a = await h.make_staff("aaaaaa")
        staff_b = await h.make_staff("bbbbbb")
        cohort_a = await h.create_cohort("Cohort A", staff_a)
        cohort_b = await h.create_cohort("Cohort B", staff_b)
        assignment_a = await h.create_assignment(cohort_a.id, "xla", staff_a)
        assignment_b = await h.create_assignment(cohort_b.id, "xla", staff_b)

        student_a = await h.make_student("100100")
        await h.cohorts.add_member(
            cohort_id=cohort_a.id, login_name="100100", actor_id=staff_a.id
        )
        await h.attempt("xla", student_a, assignment_a, completed=True)

        student_b = await h.make_student("200200")
        await h.cohorts.add_member(
            cohort_id=cohort_b.id, login_name="200200", actor_id=staff_b.id
        )
        await h.attempt("xla", student_b, assignment_b, completed=True)
        await h.attempt("xla", student_b, assignment_b, completed=False)

        result_a = await Query.cohort_analytics(
            Query(), _info(staff_a, db_session), str(cohort_a.id)
        )
        result_b = await Query.cohort_analytics(
            Query(), _info(staff_b, db_session), str(cohort_b.id)
        )

    assert result_a.total_attempts == 1
    assert result_b.total_attempts == 2
    assert result_b.completed_attempts == 1
