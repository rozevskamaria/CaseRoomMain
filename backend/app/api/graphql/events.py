from __future__ import annotations

from datetime import datetime
from typing import Any

import strawberry


@strawberry.interface
class Event:
    id: str
    seq: int
    type: str
    created_at: datetime


@strawberry.type
class SessionStartedEvent(Event):
    case_slug: str
    mode: str


@strawberry.type
class SystemMessageEvent(Event):
    message_id: str
    text: str


@strawberry.type
class StudentMessageEvent(Event):
    message_id: str
    text: str


@strawberry.type
class ScidNudgeEvent(Event):
    rng_draw: float
    parent_text: str
    tutor_text: str


@strawberry.type
class PhaseChangedEvent(Event):
    from_phase: str
    to_phase: str


@strawberry.type
class TestOrderedEvent(Event):
    key: str


@strawberry.type
class LabResultEvent(Event):
    message_id: str
    text: str
    key: str
    is_genetic: bool


@strawberry.type
class GeneticNudgeEvent(Event):
    message_id: str
    text: str


@strawberry.type
class TestUnavailableEvent(Event):
    message_id: str
    text: str
    key: str
    channel: str


@strawberry.type
class OrderBatchEvent(Event):
    message_id: str
    text: str
    any_new: bool
    channel: str


@strawberry.type
class TestOrderUnrecognizedEvent(Event):
    message_id: str
    text: str


@strawberry.type
class ParentReplyRequestedEvent(Event):
    max_tokens: int


@strawberry.type
class ParentMessageEvent(Event):
    message_id: str
    text: str


@strawberry.type
class ExamNudgeEvent(Event):
    message_id: str
    text: str


@strawberry.type
class ExamPerformedEvent(Event):
    exam_message_id: str
    exam_text: str


@strawberry.type
class ExamPathognomonicEvent(Event):
    message_id: str
    text: str


@strawberry.type
class SummarySetEvent(Event):
    value: str


@strawberry.type
class SummaryEvaluatedEvent(Event):
    tutor_message_id: str
    tutor_text: str


@strawberry.type
class DifferentialsSetEvent(Event):
    value: str


@strawberry.type
class DifferentialsEvaluatedEvent(Event):
    message_id: str
    text: str
    source: str
    wrong_key: str | None


@strawberry.type
class InterpTextSetEvent(Event):
    value: str


@strawberry.type
class InterpretationEvaluatedEvent(Event):
    interp_note_message_id: str
    interp_note_text: str
    result: str
    error: bool


@strawberry.type
class InterpretationResetEvent(Event):
    pass


@strawberry.type
class FinalAnswerFieldSetEvent(Event):
    field_name: str
    value: str


@strawberry.type
class FinalAnswerSubmittedEvent(Event):
    message_id: str
    text: str


@strawberry.type
class FeedbackGeneratedEvent(Event):
    pass


@strawberry.type
class HintRequestedEvent(Event):
    hint_text: str


@strawberry.type
class ReflectionAnsweredEvent(Event):
    step: int
    question: str
    answer: str


@strawberry.type
class ReflectionStepAdvancedEvent(Event):
    to_step: int


@strawberry.type
class ReflectionSummarizedEvent(Event):
    message_id: str
    text: str


@strawberry.type
class ModeChangedEvent(Event):
    from_mode: str
    to_mode: str


@strawberry.type
class TutorPromptEvent(Event):
    message_id: str
    text: str
    channel: str


def _base(record: Any) -> dict[str, Any]:
    return {
        "id": f"{record.seq}",
        "seq": record.seq,
        "type": record.type,
        "created_at": getattr(record, "created_at", None) or datetime.now(),
    }


def _student(record: Any, data: dict[str, Any]) -> Event:
    return StudentMessageEvent(**_base(record), message_id=data["message_id"], text=data["text"])


def _system(record: Any, data: dict[str, Any]) -> Event:
    return SystemMessageEvent(**_base(record), message_id=data["message_id"], text=data["text"])


def map_event(record: Any) -> Event:
    data = record.data or {}
    etype = record.type

    if etype == "SessionStarted":
        return SessionStartedEvent(
            **_base(record), case_slug=data["case_slug"], mode=data["mode"]
        )
    if etype == "SystemMessageAppended":
        return _system(record, data)
    if etype == "StudentMessageSent":
        return _student(record, data)
    if etype == "ScidNudgeFired":
        return ScidNudgeEvent(
            **_base(record),
            rng_draw=data["rng_draw"],
            parent_text=data["parent_text"],
            tutor_text=data["tutor_text"],
        )
    if etype == "PhaseChanged":
        return PhaseChangedEvent(
            **_base(record), from_phase=data["from_phase"], to_phase=data["to_phase"]
        )
    if etype == "TestOrdered":
        return TestOrderedEvent(**_base(record), key=data["key"])
    if etype == "LabResultShown":
        return LabResultEvent(
            **_base(record),
            message_id=data["message_id"],
            text=data["text"],
            key=data["key"],
            is_genetic=data["is_genetic"],
        )
    if etype == "GeneticNudgeShown":
        return GeneticNudgeEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "TestUnavailableNoted":
        return TestUnavailableEvent(
            **_base(record),
            message_id=data["message_id"],
            text=data["text"],
            key=data["key"],
            channel=data["channel"],
        )
    if etype == "OrderBatchNoted":
        return OrderBatchEvent(
            **_base(record),
            message_id=data["message_id"],
            text=data["text"],
            any_new=data["any_new"],
            channel=data["channel"],
        )
    if etype == "TestOrderUnrecognized":
        return TestOrderUnrecognizedEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "ParentReplyRequested":
        return ParentReplyRequestedEvent(**_base(record), max_tokens=data["max_tokens"])
    if etype == "ParentReplyAppended":
        return ParentMessageEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "ExamNudgeShown":
        return ExamNudgeEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "ExamPerformed":
        return ExamPerformedEvent(
            **_base(record),
            exam_message_id=data["exam_message_id"],
            exam_text=data["exam_text"],
        )
    if etype == "ExamPathognomonicNoted":
        return ExamPathognomonicEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "SummarySet":
        return SummarySetEvent(**_base(record), value=data["value"])
    if etype == "SummaryEvaluated":
        return SummaryEvaluatedEvent(
            **_base(record),
            tutor_message_id=data["tutor_message_id"],
            tutor_text=data["tutor_text"],
        )
    if etype == "DifferentialsSet":
        return DifferentialsSetEvent(**_base(record), value=data["value"])
    if etype == "DifferentialsEvaluated":
        return DifferentialsEvaluatedEvent(
            **_base(record),
            message_id=data["message_id"],
            text=data["text"],
            source=data["source"],
            wrong_key=data.get("wrong_key"),
        )
    if etype == "InterpTextSet":
        return InterpTextSetEvent(**_base(record), value=data["value"])
    if etype == "InterpretationEvaluated":
        return InterpretationEvaluatedEvent(
            **_base(record),
            interp_note_message_id=data["interp_note_message_id"],
            interp_note_text=data["interp_note_text"],
            result=data["result"],
            error=data["error"],
        )
    if etype == "InterpretationReset":
        return InterpretationResetEvent(**_base(record))
    if etype == "FinalAnswerFieldSet":
        return FinalAnswerFieldSetEvent(
            **_base(record), field_name=data["field_name"], value=data["value"]
        )
    if etype == "FinalAnswerSubmitted":
        return FinalAnswerSubmittedEvent(
            **_base(record), message_id=data["message_id"], text=data["ans_text"]
        )
    if etype == "FeedbackGenerated":
        return FeedbackGeneratedEvent(**_base(record))
    if etype == "HintRequested":
        return HintRequestedEvent(**_base(record), hint_text=data["hint_text"])
    if etype == "ReflectionAnswered":
        return ReflectionAnsweredEvent(
            **_base(record), step=data["step"], question=data["q"], answer=data["a"]
        )
    if etype == "ReflectionStepAdvanced":
        return ReflectionStepAdvancedEvent(**_base(record), to_step=data["to_step"])
    if etype == "ReflectionSummarized":
        return ReflectionSummarizedEvent(
            **_base(record), message_id=data["message_id"], text=data["text"]
        )
    if etype == "ModeChanged":
        return ModeChangedEvent(
            **_base(record), from_mode=data["from_mode"], to_mode=data["to_mode"]
        )
    if etype == "TutorPromptAppended":
        return TutorPromptEvent(
            **_base(record),
            message_id=data["message_id"],
            text=data["text"],
            channel=data["channel"],
        )
    raise ValueError(f"Unknown event type: {etype}")


ALL_EVENT_TYPES = [
    SessionStartedEvent,
    SystemMessageEvent,
    StudentMessageEvent,
    ScidNudgeEvent,
    PhaseChangedEvent,
    TestOrderedEvent,
    LabResultEvent,
    GeneticNudgeEvent,
    TestUnavailableEvent,
    OrderBatchEvent,
    TestOrderUnrecognizedEvent,
    ParentReplyRequestedEvent,
    ParentMessageEvent,
    ExamNudgeEvent,
    ExamPerformedEvent,
    ExamPathognomonicEvent,
    SummarySetEvent,
    SummaryEvaluatedEvent,
    DifferentialsSetEvent,
    DifferentialsEvaluatedEvent,
    InterpTextSetEvent,
    InterpretationEvaluatedEvent,
    InterpretationResetEvent,
    FinalAnswerFieldSetEvent,
    FinalAnswerSubmittedEvent,
    FeedbackGeneratedEvent,
    HintRequestedEvent,
    ReflectionAnsweredEvent,
    ReflectionStepAdvancedEvent,
    ReflectionSummarizedEvent,
    ModeChangedEvent,
    TutorPromptEvent,
]
