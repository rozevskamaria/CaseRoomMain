from __future__ import annotations

import enum
from typing import Any

import strawberry
from strawberry.fastapi import GraphQLRouter

from app import __version__
from app.api.runtime import get_session_service
from app.content.cases import get_case as content_get_case
from app.core.config import get_settings
from app.services import FinalAnswer as ServiceFinalAnswer
from app.services import Message as ServiceMessage
from app.services import Session as ServiceSession


def _require_session(session_id: str) -> ServiceSession:
    session = get_session_service().get(session_id)
    if session is None:
        raise ValueError(f"Unknown session: {session_id}")
    return session


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
    def messages(self) -> list[MessageType]:
        return [_message_type(m) for m in self._session.messages]

    @strawberry.field
    def final_answer(self) -> FinalAnswerType:
        return _final_answer_type(self._session.final_answer)

    @strawberry.field
    def feedback(self) -> FeedbackType | None:
        return _feedback_type(self._session.feedback)

    _session: strawberry.Private[ServiceSession]


@strawberry.type
class SendMessageResult:
    session: SessionType
    branch: SendBranch


@strawberry.input
class FinalAnswerInput:
    diagnosis: str = ""
    findings: str = ""
    differentials: str = ""
    tests: str = ""
    management: str = ""
    genetics: str = ""
    explanation: str = ""


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


def _session_type(session: ServiceSession) -> SessionType:
    return SessionType(
        id=session.id,
        case_id=session.case_id,
        mode=session.mode,
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
    def case(self, id: str) -> CaseType | None:
        case = content_get_case(id)
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

    @strawberry.field
    def session(self, id: str) -> SessionType | None:
        session = get_session_service().get(id)
        if session is None:
            return None
        return _session_type(session)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def start_case(self, case_id: str, mode: str) -> SessionType:
        session = get_session_service().start_case(case_id, mode)
        return _session_type(session)

    @strawberry.mutation
    def send_message(self, session_id: str, text: str) -> SendMessageResult:
        service = get_session_service()
        session = _require_session(session_id)
        result = service.send_message(session, text)
        if result.branch == "parent":
            session.pending_parent = result
        return SendMessageResult(
            session=_session_type(session),
            branch=SendBranch(result.branch),
        )

    @strawberry.mutation
    def request_exam(self, session_id: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().request_exam(session)
        return _session_type(session)

    @strawberry.mutation
    def send_test_order(self, session_id: str, text: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().send_test_order(session, text)
        return _session_type(session)

    @strawberry.mutation
    def set_summary(self, session_id: str, value: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().set_summary(session, value)
        return _session_type(session)

    @strawberry.mutation
    async def submit_summary(self, session_id: str) -> SessionType:
        session = _require_session(session_id)
        await get_session_service().submit_summary(session)
        return _session_type(session)

    @strawberry.mutation
    def set_differentials(self, session_id: str, value: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().set_differentials(session, value)
        return _session_type(session)

    @strawberry.mutation
    async def submit_differentials(self, session_id: str) -> SessionType:
        session = _require_session(session_id)
        await get_session_service().submit_differentials(session)
        return _session_type(session)

    @strawberry.mutation
    def set_interpretation(self, session_id: str, value: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().set_interp_text(session, value)
        return _session_type(session)

    @strawberry.mutation
    async def submit_interpretation(self, session_id: str) -> SessionType:
        session = _require_session(session_id)
        await get_session_service().submit_interpretation(session)
        return _session_type(session)

    @strawberry.mutation
    def set_final_answer_field(
        self, session_id: str, field_name: str, value: str
    ) -> SessionType:
        session = _require_session(session_id)
        get_session_service().set_final_answer_field(session, field_name, value)
        return _session_type(session)

    @strawberry.mutation
    async def submit_final_answer(
        self, session_id: str, answer: FinalAnswerInput | None = None
    ) -> SessionType:
        session = _require_session(session_id)
        service = get_session_service()
        if answer is not None:
            for field_name in (
                "diagnosis",
                "findings",
                "differentials",
                "tests",
                "management",
                "genetics",
                "explanation",
            ):
                service.set_final_answer_field(
                    session, field_name, getattr(answer, field_name)
                )
        await service.submit_final_answer(session)
        return _session_type(session)

    @strawberry.mutation
    async def request_hint(self, session_id: str) -> str:
        session = _require_session(session_id)
        return await get_session_service().request_hint(session)

    @strawberry.mutation
    async def submit_reflection(self, session_id: str, text: str) -> SessionType:
        session = _require_session(session_id)
        await get_session_service().submit_reflection(session, text)
        return _session_type(session)

    @strawberry.mutation
    def go_to_summary(self, session_id: str, prompt: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().go_to_summary(session, prompt)
        return _session_type(session)

    @strawberry.mutation
    def propose_differentials(self, session_id: str, prompt: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().go_to_differential(session, prompt)
        return _session_type(session)

    @strawberry.mutation
    def interpret_results(self, session_id: str, prompt: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().go_to_interpretation(session, prompt)
        return _session_type(session)

    @strawberry.mutation
    def submit_final(self, session_id: str, prompt: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().go_to_final(session, prompt)
        return _session_type(session)

    @strawberry.mutation
    def order_investigations(self, session_id: str) -> SessionType:
        session = _require_session(session_id)
        get_session_service().go_to_tests(session)
        return _session_type(session)


schema = strawberry.Schema(query=Query, mutation=Mutation)

_graphql_ide = "graphiql" if get_settings().APP_ENV == "development" else None
graphql_router: GraphQLRouter = GraphQLRouter(schema, graphql_ide=_graphql_ide)
