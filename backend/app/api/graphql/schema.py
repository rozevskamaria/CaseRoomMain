from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

import strawberry
from graphql import GraphQLError
from strawberry.exceptions import StrawberryGraphQLError
from strawberry.extensions import MaskErrors
from strawberry.fastapi import GraphQLRouter
from strawberry.scalars import JSON
from strawberry.types import Info

from app import __version__
from app.api.graphql.auth_guards import (
    AuthError,
    require_attempt_access,
    require_case_authoring_access,
    require_cohort_access,
)
from app.api.graphql.context import get_context
from app.api.graphql.events import ALL_EVENT_TYPES, Event, map_event
from app.api.graphql.permissions import (
    IsAdmin,
    IsAuthenticated,
    IsStaffOrAdmin,
    active_user,
)
from app.api.runtime import (
    get_analytics_service,
    get_authoring_service,
    get_cohort_service,
    get_session_service,
)
from app.auth import runtime as auth_runtime
from app.core.config import get_settings
from app.models.case import Case as CaseModel
from app.models.user import UserRole
from app.repositories.cohort_repo import AddMemberError, CohortAccessError
from app.services.case_authoring_service import (
    CaseAuthoringError,
    CaseSummary,
    CaseVersionView,
    LabTestSpec,
    ScalarPatch,
)
from app.schemas.case import Case as ServiceCase
from app.services import AttemptProjection as ServiceSession
from app.services import FinalAnswer as ServiceFinalAnswer
from app.services import Message as ServiceMessage


@strawberry.enum
class SendBranch(enum.Enum):
    SCID = "scid"
    TESTS = "tests"
    PARENT = "parent"


@strawberry.type
class CaseType:
    id: str
    title: str
    topic: str
    patient: str
    difficulty: str
    opening_clinical: str
    opening: str
    target_diagnosis: str
    target_iuis: str


@strawberry.type
class MessageType:
    id: str
    type: str
    text: str


@strawberry.type
class FinalAnswerType:
    diagnosis: str
    findings: str
    differentials: str
    tests: str
    management: str
    genetics: str
    explanation: str


@strawberry.type
class ScoresType:
    history_taking: str
    examination: str
    differential: str
    test_selection: str
    interpretation: str
    management: str


@strawberry.type
class FeedbackType:
    diagnostic_accuracy: str
    diagnostic_comment: str
    well_done: list[str]
    missing: list[str]
    key_clues: list[str]
    reasoning_pathway: str
    management_points: list[str]
    genetic_points: list[str]
    revision_topic: str
    scores: ScoresType | None


@strawberry.type
class SessionType:
    id: str
    case_id: str
    mode: str
    language: str
    phase: str
    hints_used: int
    exam_done: bool
    summary: str
    differentials: str
    interp_text: str
    interp_result: str
    reflection_step: int

    @strawberry.field
    def ordered_tests(self) -> list[str]:
        return sorted(self._session.ordered_tests)

    @strawberry.field
    async def messages(self, info: Info) -> list[MessageType]:
        await require_attempt_access(info, self.id, write=False)
        return [_message_type(m) for m in self._session.messages]

    @strawberry.field
    def final_answer(self) -> FinalAnswerType:
        return _final_answer_type(self._session.final_answer)

    @strawberry.field
    async def feedback(self, info: Info) -> FeedbackType | None:
        await require_attempt_access(info, self.id, write=False)
        return _feedback_type(self._session.feedback)

    _session: strawberry.Private[ServiceSession]


@strawberry.type
class AttemptType:
    id: str
    case_id: str
    mode: str
    phase: str
    status: str
    started_at: datetime
    completed_at: datetime | None

    @strawberry.field
    async def events(self, info: Info) -> list[Event]:
        await require_attempt_access(info, self.id, write=False)
        records = await info.context.events_loader.load(self.id)
        return [map_event(r) for r in records]

    @strawberry.field
    async def feedback(self, info: Info) -> FeedbackType | None:
        await require_attempt_access(info, self.id, write=False)
        session = await get_session_service().get(self.id)
        if session is None:
            return None
        return _feedback_type(session.feedback)


@strawberry.type
class SendMessageResult:
    session: SessionType
    branch: SendBranch


@strawberry.type
class MeType:
    id: str
    role: str
    status: str
    login_name: str
    email: str | None
    full_name: str | None


@strawberry.type
class AuthResult:
    ok: bool


@strawberry.type
class ConsumeResultType:
    ok: bool
    reason: str | None


@strawberry.input
class FinalAnswerInput:
    diagnosis: str = ""
    findings: str = ""
    differentials: str = ""
    tests: str = ""
    management: str = ""
    genetics: str = ""
    explanation: str = ""


@strawberry.type
class AssignmentType:
    id: str
    cohort_id: str
    case_id: str
    case_version_id: str
    title: str | None
    mode: str
    language: str
    opens_at: datetime | None
    due_at: datetime | None
    created_at: datetime


@strawberry.type
class CohortStudentType:
    cohort_id: str
    joined_at: datetime
    _user: strawberry.Private[Any]

    @strawberry.field
    async def user(self, info: Info) -> MeType:
        return await _me_from_user(info, self._user)

    @strawberry.field
    async def attempts(self, info: Info) -> list[AttemptType]:
        await require_cohort_access(info, self.cohort_id, write=False)
        records = await info.context.attempts_by_student_loader.load(
            (self.cohort_id, str(self._user.id))
        )
        return [_attempt_type_from_model(a, slug) for a, slug in records]


@strawberry.type
class CohortType:
    id: str
    name: str
    academic_year: str | None
    archived: bool
    created_at: datetime

    @strawberry.field
    async def student_count(self, info: Info) -> int:
        await require_cohort_access(info, self.id, write=False)
        rows = await info.context.students_by_cohort_loader.load(self.id)
        return len(rows)

    @strawberry.field
    async def students(self, info: Info) -> list[CohortStudentType]:
        await require_cohort_access(info, self.id, write=False)
        rows = await info.context.students_by_cohort_loader.load(self.id)
        return [
            CohortStudentType(
                cohort_id=self.id, joined_at=row.joined_at, _user=row.user
            )
            for row in rows
        ]

    @strawberry.field
    async def staff(self, info: Info) -> list[MeType]:
        await require_cohort_access(info, self.id, write=False)
        rows = await info.context.staff_by_cohort_loader.load(self.id)
        return [await _me_from_user(info, user) for user in rows]

    @strawberry.field
    async def assignments(self, info: Info) -> list[AssignmentType]:
        await require_cohort_access(info, self.id, write=False)
        rows = await info.context.assignments_by_cohort_loader.load(self.id)
        return [_assignment_type(a) for a in rows]


@strawberry.type
class CohortMembershipResult:
    cohort: CohortType
    student: MeType


@strawberry.type
class AddStudentResult:
    status: str
    cohort: CohortType | None
    student: MeType | None


@strawberry.type
class StudentLookupResult:
    status: str
    full_name: str | None


@strawberry.type
class CohortAuditEntry:
    id: str
    actor_id: str | None
    subject_id: str | None
    action: str
    created_at: datetime


@strawberry.type
class CohortAnalyticsType:
    cohort_id: str
    total_attempts: int
    completed_attempts: int
    completion_rate: float
    attempts_per_case: JSON
    score_distribution: JSON
    diagnostic_accuracy_distribution: JSON
    wrong_path_frequency: JSON


def _cohort_analytics_type(analytics) -> CohortAnalyticsType:
    return CohortAnalyticsType(
        cohort_id=analytics.cohort_id,
        total_attempts=analytics.total_attempts,
        completed_attempts=analytics.completed_attempts,
        completion_rate=analytics.completion_rate,
        attempts_per_case=analytics.attempts_per_case,
        score_distribution=analytics.score_distribution,
        diagnostic_accuracy_distribution=(
            analytics.diagnostic_accuracy_distribution
        ),
        wrong_path_frequency=analytics.wrong_path_frequency,
    )


@strawberry.input
class CreateCohortInput:
    name: str
    academic_year: str | None = None


@strawberry.input
class CreateAssignmentInput:
    cohort_id: str
    case_id: str
    mode: str
    language: str | None = None
    title: str | None = None
    opens_at: datetime | None = None
    due_at: datetime | None = None


def _cohort_type(cohort) -> CohortType:
    return CohortType(
        id=str(cohort.id),
        name=cohort.name,
        academic_year=cohort.academic_year,
        archived=cohort.archived,
        created_at=cohort.created_at,
    )


def _assignment_type(assignment) -> AssignmentType:
    return AssignmentType(
        id=str(assignment.id),
        cohort_id=str(assignment.cohort_id),
        case_id=str(assignment.case_id),
        case_version_id=str(assignment.case_version_id),
        title=assignment.title,
        mode=assignment.mode,
        language=assignment.language.value,
        opens_at=assignment.opens_at,
        due_at=assignment.due_at,
        created_at=assignment.created_at,
    )


def _attempt_type_from_model(attempt, case_slug: str) -> AttemptType:
    return AttemptType(
        id=str(attempt.id),
        case_id=case_slug,
        mode=attempt.mode,
        phase=attempt.phase,
        status=attempt.status.value,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
    )


def _message_type(message: ServiceMessage) -> MessageType:
    return MessageType(id=message.id, type=message.type, text=message.text)


def _final_answer_type(answer: ServiceFinalAnswer) -> FinalAnswerType:
    return FinalAnswerType(
        diagnosis=answer.diagnosis,
        findings=answer.findings,
        differentials=answer.differentials,
        tests=answer.tests,
        management=answer.management,
        genetics=answer.genetics,
        explanation=answer.explanation,
    )


def _scores_type(scores: dict[str, Any] | None) -> ScoresType | None:
    if not scores:
        return None
    return ScoresType(
        history_taking=scores.get("historyTaking", ""),
        examination=scores.get("examination", ""),
        differential=scores.get("differential", ""),
        test_selection=scores.get("testSelection", ""),
        interpretation=scores.get("interpretation", ""),
        management=scores.get("management", ""),
    )


def _feedback_type(feedback: dict[str, Any] | None) -> FeedbackType | None:
    if feedback is None:
        return None
    return FeedbackType(
        diagnostic_accuracy=feedback.get("diagnosticAccuracy", ""),
        diagnostic_comment=feedback.get("diagnosticComment", ""),
        well_done=list(feedback.get("wellDone", [])),
        missing=list(feedback.get("missing", [])),
        key_clues=list(feedback.get("keyClues", [])),
        reasoning_pathway=feedback.get("reasoningPathway", ""),
        management_points=list(feedback.get("managementPoints", [])),
        genetic_points=list(feedback.get("geneticPoints", [])),
        revision_topic=feedback.get("revisionTopic", ""),
        scores=_scores_type(feedback.get("scores")),
    )


def _client_ip(info: Info) -> str | None:
    request = getattr(info.context, "request", None)
    if request is None or request.client is None:
        return None
    return request.client.host


def _background(info: Info):
    tasks = getattr(info.context, "background_tasks", None)
    if tasks is None:
        return None

    def schedule(coro_factory):
        tasks.add_task(coro_factory)

    return schedule


async def _me_from_user(info: Info, user) -> MeType:
    store = auth_runtime.get_user_store(getattr(info.context, "db_session", None))
    decrypt_profile = getattr(store, "decrypt_profile", None)
    if decrypt_profile is not None:
        login_name, email, full_name = await decrypt_profile(user)
    else:
        login_name = user.login_name
        email = user.email
        full_name = user.full_name
    return MeType(
        id=str(user.id),
        role=user.role.value,
        status=user.status.value,
        login_name=login_name,
        email=email,
        full_name=full_name,
    )


def _session_type(session: ServiceSession) -> SessionType:
    return SessionType(
        id=session.id,
        case_id=session.case_id,
        mode=session.mode,
        language=session.language,
        phase=session.phase,
        hints_used=session.hints_used,
        exam_done=session.exam_done,
        summary=session.summary,
        differentials=session.differentials,
        interp_text=session.interp_text,
        interp_result=session.interp_result,
        reflection_step=session.reflection_step,
        _session=session,
    )


@strawberry.input
class DraftScalarsInput:
    difficulty: str | None = None
    target_diagnosis: str | None = None
    topic: str | None = None
    iuis: str | None = None


@strawberry.input
class LabTestInput:
    key: str
    kind: str
    result_by_language: JSON


@strawberry.input
class SetDraftLabDataInput:
    version_id: str
    language: str
    tests: list[LabTestInput]


@strawberry.type
class CaseSummaryType:
    case_id: str
    slug: str
    version_id: str
    version_no: int
    status: str
    is_current: bool
    difficulty: str
    topic: str
    target_diagnosis: str
    iuis: str
    has_lv: bool


@strawberry.type
class CaseLocalizationType:
    language: str
    content: JSON


@strawberry.type
class CaseTestType:
    key: str
    kind: str
    ord: int


@strawberry.type
class CaseVersionType:
    case_id: str
    slug: str
    version_id: str
    version_no: int
    status: str
    is_current: bool
    difficulty: str
    topic: str
    target_diagnosis: str
    iuis: str
    localizations: list[CaseLocalizationType]
    tests: list[CaseTestType]


@strawberry.type
class CasePreviewType:
    id: str
    title: str
    topic: str
    patient: str
    difficulty: str
    opening_clinical: str
    opening: str
    target_diagnosis: str
    target_iuis: str
    red_flags: list[str]
    parent_prompt: str
    lab_data: JSON
    exam_findings: str
    model_diagnosis: str
    model_management: str
    model_genetic_counselling: str
    key_clues: list[str]
    wrong_paths: JSON


@strawberry.type
class PublishResultType:
    version: CaseVersionType


@strawberry.type
class DiscardDraftResult:
    case_id: str
    deleted_case: bool


def _case_summary_type(summary: CaseSummary) -> CaseSummaryType:
    return CaseSummaryType(
        case_id=summary.case_id,
        slug=summary.slug,
        version_id=summary.version_id,
        version_no=summary.version_no,
        status=summary.status,
        is_current=summary.is_current,
        difficulty=summary.difficulty,
        topic=summary.topic,
        target_diagnosis=summary.target_diagnosis,
        iuis=summary.iuis,
        has_lv=summary.has_lv,
    )


def _case_version_type(view: CaseVersionView) -> CaseVersionType:
    return CaseVersionType(
        case_id=view.case_id,
        slug=view.slug,
        version_id=view.version_id,
        version_no=view.version_no,
        status=view.status,
        is_current=view.is_current,
        difficulty=view.difficulty,
        topic=view.topic,
        target_diagnosis=view.target_diagnosis,
        iuis=view.iuis,
        localizations=[
            CaseLocalizationType(language=loc.language, content=loc.content)
            for loc in view.localizations
        ],
        tests=[
            CaseTestType(key=t.key, kind=t.kind, ord=t.ord) for t in view.tests
        ],
    )


def _case_preview_type(case: ServiceCase) -> CasePreviewType:
    return CasePreviewType(
        id=case.id,
        title=case.title,
        topic=case.topic,
        patient=case.patient,
        difficulty=case.difficulty,
        opening_clinical=case.opening_clinical,
        opening=case.opening,
        target_diagnosis=case.target_diagnosis,
        target_iuis=case.target_iuis,
        red_flags=list(case.red_flags),
        parent_prompt=case.parent_prompt,
        lab_data=dict(case.lab_data),
        exam_findings=case.exam_findings,
        model_diagnosis=case.model_diagnosis,
        model_management=case.model_management,
        model_genetic_counselling=case.model_genetic_counselling,
        key_clues=list(case.key_clues),
        wrong_paths=dict(case.wrong_paths),
    )


def _authoring_error(exc: CaseAuthoringError) -> AuthError:
    if exc.fields:
        return AuthError(f"{exc.code}: {', '.join(exc.fields)}")
    return AuthError(exc.code)


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong"

    @strawberry.field
    def version(self) -> str:
        return __version__

    @strawberry.field
    def health(self) -> str:
        return "ok"

    @strawberry.field
    async def me(self, info: Info) -> MeType | None:
        user = active_user(info)
        if user is None:
            return None
        return await _me_from_user(info, user)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def case(self, id: str) -> CaseType | None:
        case = await get_session_service().get_case(id)
        if case is None:
            return None
        return CaseType(
            id=case.id,
            title=case.title,
            topic=case.topic,
            patient=case.patient,
            difficulty=case.difficulty,
            opening_clinical=case.opening_clinical,
            opening=case.opening,
            target_diagnosis=case.target_diagnosis,
            target_iuis=case.target_iuis,
        )

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def session(self, info: Info, id: str) -> SessionType | None:
        await require_attempt_access(info, id, write=False)
        session = await get_session_service().get(id)
        if session is None:
            return None
        return _session_type(session)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def attempt(self, info: Info, id: str) -> AttemptType | None:
        await require_attempt_access(info, id, write=False)
        service = get_session_service()
        session = await service.get(id)
        if session is None:
            return None
        meta = await service.get_attempt_meta(id)
        if meta is not None:
            status = meta.status
            started_at = meta.started_at
            completed_at = meta.completed_at
        else:
            status = (
                "completed" if session.phase == "feedback" else "in_progress"
            )
            started_at = datetime.now()
            completed_at = None
        return AttemptType(
            id=session.id,
            case_id=session.case_id,
            mode=session.mode,
            phase=session.phase,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
        )

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def my_cohorts(self, info: Info) -> list[CohortType]:
        user = active_user(info)
        is_admin = user.role == UserRole.admin
        cohorts = await info.context.cohorts_for_user_loader.load(
            (str(user.id), is_admin)
        )
        return [_cohort_type(c) for c in cohorts]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def cohort(self, info: Info, id: str) -> CohortType | None:
        cohort = await get_cohort_service().get_cohort(id)
        if cohort is None:
            return None
        await require_cohort_access(info, id, write=False)
        return _cohort_type(cohort)

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def cohort_roster(
        self, info: Info, cohort_id: str
    ) -> list[CohortStudentType]:
        await require_cohort_access(info, cohort_id, write=False)
        rows = await info.context.students_by_cohort_loader.load(cohort_id)
        return [
            CohortStudentType(
                cohort_id=cohort_id, joined_at=row.joined_at, _user=row.user
            )
            for row in rows
        ]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def cohort_student(
        self, info: Info, cohort_id: str, student_id: str
    ) -> CohortStudentType | None:
        await require_cohort_access(info, cohort_id, write=False)
        member = await get_cohort_service().get_member(cohort_id, student_id)
        if member is None:
            raise AuthError("Forbidden")
        return CohortStudentType(
            cohort_id=cohort_id, joined_at=member.joined_at, _user=member.user
        )

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def student_attempts(
        self, info: Info, cohort_id: str, student_id: str
    ) -> list[AttemptType]:
        await require_cohort_access(info, cohort_id, write=False)
        if not await get_cohort_service().member_active(cohort_id, student_id):
            raise AuthError("Forbidden")
        records = await info.context.attempts_by_student_loader.load(
            (cohort_id, student_id)
        )
        return [_attempt_type_from_model(a, slug) for a, slug in records]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def assignments_for_cohort(
        self, info: Info, cohort_id: str
    ) -> list[AssignmentType]:
        await require_cohort_access(info, cohort_id, write=False)
        rows = await info.context.assignments_by_cohort_loader.load(cohort_id)
        return [_assignment_type(a) for a in rows]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def cohort_analytics(
        self, info: Info, cohort_id: str
    ) -> CohortAnalyticsType:
        await require_cohort_access(info, cohort_id, write=False)
        analytics = await get_analytics_service().cohort_analytics(cohort_id)
        return _cohort_analytics_type(analytics)

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def lookup_student(
        self, info: Info, cohort_id: str, login_name: str
    ) -> StudentLookupResult:
        await require_cohort_access(info, cohort_id, write=False)
        result = await get_cohort_service().lookup_student(
            cohort_id=cohort_id, login_name=login_name
        )
        full_name = None
        if result.user is not None and result.status in (
            "enrollable",
            "already_enrolled",
        ):
            full_name = await get_cohort_service().decrypt(result.user.full_name)
        return StudentLookupResult(status=result.status, full_name=full_name)

    @strawberry.field(permission_classes=[IsAdmin])
    async def cohort_audit_log(
        self, info: Info, cohort_id: str
    ) -> list[CohortAuditEntry]:
        entries = await get_cohort_service().audit_for_cohort(cohort_id)
        return [
            CohortAuditEntry(
                id=str(entry.id),
                actor_id=str(entry.actor_id) if entry.actor_id else None,
                subject_id=str(entry.subject_id) if entry.subject_id else None,
                action=entry.action.value,
                created_at=entry.created_at,
            )
            for entry in entries
        ]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def author_cases(self, info: Info) -> list[CaseSummaryType]:
        require_case_authoring_access(info)
        summaries = await get_authoring_service().list_cases()
        return [_case_summary_type(s) for s in summaries]

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def case_draft(
        self, info: Info, version_id: str
    ) -> CaseVersionType | None:
        require_case_authoring_access(info)
        view = await get_authoring_service().get_draft(uuid.UUID(version_id))
        if view is None:
            return None
        return _case_version_type(view)

    @strawberry.field(permission_classes=[IsStaffOrAdmin])
    async def preview_case(
        self, info: Info, version_id: str, language: str = "en"
    ) -> CasePreviewType | None:
        require_case_authoring_access(info)
        case = await get_authoring_service().preview(
            uuid.UUID(version_id), language
        )
        if case is None:
            return None
        return _case_preview_type(case)


@strawberry.type
class Mutation:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def start_case(self, info: Info, case_id: str, mode: str) -> SessionType:
        user = active_user(info)
        session = await get_session_service().start_case(
            case_id, mode, student_id=str(user.id)
        )
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def start_case_localized(
        self, info: Info, case_id: str, mode: str, language: str
    ) -> SessionType:
        user = active_user(info)
        session = await get_session_service().start_case(
            case_id, mode, student_id=str(user.id), language=language
        )
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def send_message(
        self, info: Info, session_id: str, text: str
    ) -> SendMessageResult:
        await require_attempt_access(info, session_id, write=True)
        service = get_session_service()
        result, session = await service.send_message(session_id, text)
        return SendMessageResult(
            session=_session_type(session),
            branch=SendBranch(result.branch),
        )

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def request_exam(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().request_exam(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def send_test_order(
        self, info: Info, session_id: str, text: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().send_test_order(session_id, text)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_summary(
        self, info: Info, session_id: str, value: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().set_summary(session_id, value)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_summary(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().submit_summary(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_differentials(
        self, info: Info, session_id: str, value: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().set_differentials(session_id, value)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_differentials(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().submit_differentials(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_interpretation(
        self, info: Info, session_id: str, value: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().set_interp_text(session_id, value)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_interpretation(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().submit_interpretation(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def set_final_answer_field(
        self, info: Info, session_id: str, field_name: str, value: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().set_final_answer_field(
            session_id, field_name, value
        )
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_final_answer(
        self, info: Info, session_id: str, answer: FinalAnswerInput | None = None
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        service = get_session_service()
        if answer is not None:
            await service.set_final_answer_fields(
                session_id,
                {
                    field_name: getattr(answer, field_name)
                    for field_name in (
                        "diagnosis",
                        "findings",
                        "differentials",
                        "tests",
                        "management",
                        "genetics",
                        "explanation",
                    )
                },
            )
        session = await service.submit_final_answer(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def request_hint(self, info: Info, session_id: str) -> str:
        await require_attempt_access(info, session_id, write=True)
        return await get_session_service().request_hint(session_id)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_reflection(
        self, info: Info, session_id: str, text: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().submit_reflection(session_id, text)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def go_to_summary(
        self, info: Info, session_id: str, prompt: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_summary(session_id, prompt)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def propose_differentials(
        self, info: Info, session_id: str, prompt: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_differential(session_id, prompt)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def interpret_results(
        self, info: Info, session_id: str, prompt: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_interpretation(session_id, prompt)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def submit_final(
        self, info: Info, session_id: str, prompt: str
    ) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_final(session_id, prompt)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def order_investigations(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_tests(session_id)
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def reflect(self, info: Info, session_id: str) -> SessionType:
        await require_attempt_access(info, session_id, write=True)
        session = await get_session_service().go_to_reflection(session_id)
        return _session_type(session)

    @strawberry.mutation
    async def request_login_link(self, info: Info, login_name: str) -> AuthResult:
        svc = auth_runtime.build_auth_service(
            getattr(info.context, "db_session", None),
            background=_background(info),
        )
        result = await svc.request_link(login_name, _client_ip(info))
        return AuthResult(ok=result.ok)

    @strawberry.mutation
    async def register_student(
        self, info: Info, login_name: str, full_name: str | None = None
    ) -> AuthResult:
        svc = auth_runtime.build_auth_service(
            getattr(info.context, "db_session", None),
            background=_background(info),
        )
        result = await svc.register_student(login_name, full_name, _client_ip(info))
        return AuthResult(ok=result.ok)

    @strawberry.mutation
    async def consume_magic_link(
        self, info: Info, token: str
    ) -> ConsumeResultType:
        svc = auth_runtime.build_auth_service(
            getattr(info.context, "db_session", None)
        )
        result = await svc.consume_link(token, _client_ip(info))
        if not result.ok:
            return ConsumeResultType(ok=False, reason=result.reason)
        settings = get_settings()
        info.context.response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=result.session_id,
            max_age=settings.SESSION_TTL_SECONDS,
            httponly=True,
            secure=settings.APP_ENV == "production",
            samesite="lax",
            path="/",
        )
        return ConsumeResultType(ok=True, reason=None)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def logout(self, info: Info) -> AuthResult:
        settings = get_settings()
        sid = info.context.request.cookies.get(settings.SESSION_COOKIE_NAME)
        svc = auth_runtime.build_auth_service(
            getattr(info.context, "db_session", None)
        )
        await svc.logout(sid)
        info.context.response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
        return AuthResult(ok=True)

    @strawberry.mutation(permission_classes=[IsAdmin])
    async def create_staff(
        self,
        info: Info,
        login_name: str,
        email: str,
        full_name: str | None,
        role: str,
    ) -> MeType:
        svc = auth_runtime.build_auth_service(
            getattr(info.context, "db_session", None),
            background=_background(info),
        )
        user = await svc.create_staff(login_name, email, full_name, UserRole(role))
        return await _me_from_user(info, user)

    @strawberry.mutation
    async def dev_login(self, info: Info, login_name: str) -> ConsumeResultType:
        if get_settings().APP_ENV != "development":
            return ConsumeResultType(ok=False, reason="disabled")
        session_id = await auth_runtime.dev_login(
            getattr(info.context, "db_session", None), login_name
        )
        settings = get_settings()
        info.context.response.set_cookie(
            key=settings.SESSION_COOKIE_NAME,
            value=session_id,
            max_age=settings.SESSION_TTL_SECONDS,
            httponly=True,
            secure=False,
            samesite="lax",
            path="/",
        )
        return ConsumeResultType(ok=True, reason=None)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def create_cohort(
        self, info: Info, input: CreateCohortInput
    ) -> CohortType:
        user = active_user(info)
        cohort = await get_cohort_service().create_cohort(
            name=input.name,
            academic_year=input.academic_year,
            created_by=str(user.id),
        )
        return _cohort_type(cohort)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def add_student_to_cohort(
        self, info: Info, cohort_id: str, login_name: str
    ) -> AddStudentResult:
        await require_cohort_access(info, cohort_id, write=True)
        user = active_user(info)
        try:
            outcome = await get_cohort_service().add_member(
                cohort_id=cohort_id,
                login_name=login_name,
                actor_id=str(user.id),
            )
        except AddMemberError as exc:
            return AddStudentResult(
                status=exc.status, cohort=None, student=None
            )
        return AddStudentResult(
            status="enrolled",
            cohort=_cohort_type(outcome.cohort),
            student=await _me_from_user(info, outcome.student),
        )

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def remove_student_from_cohort(
        self, info: Info, cohort_id: str, student_id: str
    ) -> CohortMembershipResult:
        await require_cohort_access(info, cohort_id, write=True)
        user = active_user(info)
        try:
            outcome = await get_cohort_service().remove_member(
                cohort_id=cohort_id,
                student_id=student_id,
                actor_id=str(user.id),
            )
        except AddMemberError as exc:
            raise AuthError(exc.status) from exc
        return CohortMembershipResult(
            cohort=_cohort_type(outcome.cohort),
            student=await _me_from_user(info, outcome.student),
        )

    @strawberry.mutation(permission_classes=[IsAdmin])
    async def assign_staff_to_cohort(
        self, info: Info, cohort_id: str, staff_id: str
    ) -> CohortType:
        user = active_user(info)
        try:
            cohort = await get_cohort_service().assign_staff(
                cohort_id=cohort_id, staff_id=staff_id, actor_id=str(user.id)
            )
        except CohortAccessError as exc:
            raise AuthError(str(exc)) from exc
        return _cohort_type(cohort)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def create_assignment(
        self, info: Info, input: CreateAssignmentInput
    ) -> AssignmentType:
        await require_cohort_access(info, input.cohort_id, write=True)
        user = active_user(info)
        try:
            assignment = await get_cohort_service().create_assignment(
                cohort_id=input.cohort_id,
                case_id=input.case_id,
                mode=input.mode,
                language=input.language or "en",
                title=input.title,
                opens_at=input.opens_at,
                due_at=input.due_at,
                created_by=str(user.id),
            )
        except CohortAccessError as exc:
            raise AuthError(str(exc)) from exc
        return _assignment_type(assignment)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def start_assignment_attempt(
        self, info: Info, assignment_id: str
    ) -> SessionType:
        user = active_user(info)
        cohort_service = get_cohort_service()
        assignment = await cohort_service.get_assignment(assignment_id)
        if assignment is None:
            raise AuthError("Unknown assignment")
        if not await cohort_service.member_active(
            str(assignment.cohort_id), str(user.id)
        ):
            raise AuthError("Forbidden")
        case_model = await info.context.db_session.get(
            CaseModel, assignment.case_id
        )
        if case_model is None:
            raise AuthError("Unknown assignment")
        session = await get_session_service().start_case(
            case_model.slug,
            assignment.mode,
            student_id=str(user.id),
            language=assignment.language.value,
            assignment_id=assignment_id,
        )
        return _session_type(session)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def create_case_draft(
        self,
        info: Info,
        slug: str | None = None,
        from_version_id: str | None = None,
    ) -> CaseVersionType:
        require_case_authoring_access(info)
        user = active_user(info)
        try:
            view = await get_authoring_service().create_case_draft(
                slug=slug,
                from_version_id=(
                    uuid.UUID(from_version_id)
                    if from_version_id is not None
                    else None
                ),
                created_by=uuid.UUID(str(user.id)),
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return _case_version_type(view)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def set_case_draft_scalars(
        self, info: Info, version_id: str, input: DraftScalarsInput
    ) -> CaseVersionType:
        require_case_authoring_access(info)
        try:
            view = await get_authoring_service().set_draft_scalars(
                uuid.UUID(version_id),
                ScalarPatch(
                    difficulty=input.difficulty,
                    target_diagnosis=input.target_diagnosis,
                    topic=input.topic,
                    iuis=input.iuis,
                ),
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return _case_version_type(view)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def set_case_draft_localization(
        self, info: Info, version_id: str, language: str, content: JSON
    ) -> CaseVersionType:
        require_case_authoring_access(info)
        try:
            view = await get_authoring_service().set_draft_localization(
                uuid.UUID(version_id), language, dict(content)
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return _case_version_type(view)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def set_case_draft_lab_data(
        self, info: Info, input: SetDraftLabDataInput
    ) -> CaseVersionType:
        require_case_authoring_access(info)
        specs = [
            LabTestSpec(
                key=t.key,
                kind=t.kind,
                result_by_language=dict(t.result_by_language),
            )
            for t in input.tests
        ]
        try:
            view = await get_authoring_service().set_draft_lab_data(
                uuid.UUID(input.version_id), input.language, specs
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return _case_version_type(view)

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def publish_case_version(
        self, info: Info, version_id: str
    ) -> PublishResultType:
        require_case_authoring_access(info)
        try:
            result = await get_authoring_service().publish_version(
                uuid.UUID(version_id)
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return PublishResultType(version=_case_version_type(result.version))

    @strawberry.mutation(permission_classes=[IsStaffOrAdmin])
    async def discard_case_draft(
        self, info: Info, version_id: str
    ) -> DiscardDraftResult:
        require_case_authoring_access(info)
        try:
            result = await get_authoring_service().discard_draft(
                uuid.UUID(version_id)
            )
        except CaseAuthoringError as exc:
            raise _authoring_error(exc) from exc
        return DiscardDraftResult(
            case_id=result.case_id, deleted_case=result.deleted_case
        )


def _should_mask_error(error: GraphQLError) -> bool:
    original = error.original_error
    if original is None:
        return False
    return not isinstance(original, (StrawberryGraphQLError, ValueError, KeyError))


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=ALL_EVENT_TYPES,
    extensions=[lambda: MaskErrors(should_mask_error=_should_mask_error)],
)

_graphql_ide = "graphiql" if get_settings().APP_ENV == "development" else None
graphql_router: GraphQLRouter = GraphQLRouter(
    schema, graphql_ide=_graphql_ide, context_getter=get_context
)
