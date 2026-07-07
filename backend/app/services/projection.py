from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

Mode = Literal["practice", "exam", "reflection"]
MessageType = Literal[
    "parent", "tutor", "student", "system", "lab", "lab_note", "lab_tutor"
]

EXAM_STUDENT_MSG = "I would like to perform a physical examination."


@dataclass
class Message:
    id: str
    type: MessageType
    text: str


@dataclass
class FinalAnswer:
    diagnosis: str = ""
    findings: str = ""
    differentials: str = ""
    tests: str = ""
    management: str = ""
    genetics: str = ""
    explanation: str = ""


@dataclass
class SendResult:
    branch: Literal["scid", "tests", "parent"]
    system: str | None = None
    messages: list[dict] | None = None
    max_tokens: int | None = None


class EventType(str, Enum):
    SESSION_STARTED = "SessionStarted"
    SYSTEM_MESSAGE_APPENDED = "SystemMessageAppended"
    STUDENT_MESSAGE_SENT = "StudentMessageSent"
    SCID_NUDGE_FIRED = "ScidNudgeFired"
    PHASE_CHANGED = "PhaseChanged"
    TEST_ORDERED = "TestOrdered"
    LAB_RESULT_SHOWN = "LabResultShown"
    GENETIC_NUDGE_SHOWN = "GeneticNudgeShown"
    TEST_UNAVAILABLE_NOTED = "TestUnavailableNoted"
    ORDER_BATCH_NOTED = "OrderBatchNoted"
    TEST_ORDER_UNRECOGNIZED = "TestOrderUnrecognized"
    PARENT_REPLY_REQUESTED = "ParentReplyRequested"
    PARENT_REPLY_APPENDED = "ParentReplyAppended"
    EXAM_NUDGE_SHOWN = "ExamNudgeShown"
    EXAM_PERFORMED = "ExamPerformed"
    EXAM_PATHOGNOMONIC_NOTED = "ExamPathognomonicNoted"
    SUMMARY_SET = "SummarySet"
    SUMMARY_EVALUATED = "SummaryEvaluated"
    DIFFERENTIALS_SET = "DifferentialsSet"
    DIFFERENTIALS_EVALUATED = "DifferentialsEvaluated"
    INTERP_TEXT_SET = "InterpTextSet"
    INTERPRETATION_EVALUATED = "InterpretationEvaluated"
    INTERPRETATION_RESET = "InterpretationReset"
    FINAL_ANSWER_FIELD_SET = "FinalAnswerFieldSet"
    FINAL_ANSWER_SUBMITTED = "FinalAnswerSubmitted"
    FEEDBACK_GENERATED = "FeedbackGenerated"
    HINT_REQUESTED = "HintRequested"
    REFLECTION_ANSWERED = "ReflectionAnswered"
    REFLECTION_STEP_ADVANCED = "ReflectionStepAdvanced"
    REFLECTION_SUMMARIZED = "ReflectionSummarized"
    MODE_CHANGED = "ModeChanged"
    TUTOR_PROMPT_APPENDED = "TutorPromptAppended"


@dataclass
class EventRecord:
    type: str
    seq: int
    data: dict[str, Any]


@dataclass
class NewEvent:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class AttemptProjection:
    id: str = ""
    case_id: str = ""
    mode: Mode = "practice"
    language: str = "en"
    phase: str = "history"
    messages: list[Message] = field(default_factory=list)
    hints_used: int = 0
    ordered_tests: set[str] = field(default_factory=set)
    exam_done: bool = False
    summary: str = ""
    differentials: str = ""
    final_answer: FinalAnswer = field(default_factory=FinalAnswer)
    feedback: dict | None = None
    reflection_step: int = 0
    reflection_answers: list[dict] = field(default_factory=list)
    interp_text: str = ""
    interp_result: str = ""
    pending_parent: SendResult | None = None


def _append(proj: AttemptProjection, message_id: str, type: str, text: str) -> None:
    proj.messages.append(Message(id=message_id, type=type, text=text))


def fold(events: list[EventRecord]) -> AttemptProjection:
    proj = AttemptProjection()
    for event in sorted(events, key=lambda e: e.seq):
        data = event.data
        etype = event.type

        if etype == EventType.SESSION_STARTED:
            proj.id = data["id"]
            proj.case_id = data["case_slug"]
            proj.mode = data["mode"]
            proj.language = data.get("language", "en")
            proj.phase = "history"
        elif etype == EventType.SYSTEM_MESSAGE_APPENDED:
            _append(proj, data["message_id"], "system", data["text"])
        elif etype == EventType.STUDENT_MESSAGE_SENT:
            _append(proj, data["message_id"], "student", data["text"])
        elif etype == EventType.SCID_NUDGE_FIRED:
            _append(proj, data["parent_message_id"], "parent", data["parent_text"])
            _append(proj, data["tutor_message_id"], "tutor", data["tutor_text"])
        elif etype == EventType.PHASE_CHANGED:
            proj.phase = data["to_phase"]
        elif etype == EventType.TEST_ORDERED:
            proj.ordered_tests.add(data["key"])
        elif etype == EventType.LAB_RESULT_SHOWN:
            _append(proj, data["message_id"], "lab", data["text"])
        elif etype == EventType.GENETIC_NUDGE_SHOWN:
            _append(proj, data["message_id"], "lab_tutor", data["text"])
        elif etype == EventType.TEST_UNAVAILABLE_NOTED:
            _append(proj, data["message_id"], data["channel"], data["text"])
        elif etype == EventType.ORDER_BATCH_NOTED:
            _append(proj, data["message_id"], data["channel"], data["text"])
        elif etype == EventType.TEST_ORDER_UNRECOGNIZED:
            _append(proj, data["message_id"], "lab_note", data["text"])
        elif etype == EventType.PARENT_REPLY_REQUESTED:
            pass
        elif etype == EventType.PARENT_REPLY_APPENDED:
            _append(proj, data["message_id"], "parent", data["text"])
        elif etype == EventType.EXAM_NUDGE_SHOWN:
            _append(proj, data["message_id"], "tutor", data["text"])
        elif etype == EventType.EXAM_PERFORMED:
            _append(proj, data["student_message_id"], "student", EXAM_STUDENT_MSG)
            _append(proj, data["exam_message_id"], "system", data["exam_text"])
            proj.exam_done = True
        elif etype == EventType.EXAM_PATHOGNOMONIC_NOTED:
            _append(proj, data["message_id"], "tutor", data["text"])
        elif etype == EventType.SUMMARY_SET:
            proj.summary = data["value"]
        elif etype == EventType.SUMMARY_EVALUATED:
            _append(proj, data["tutor_message_id"], "tutor", data["tutor_text"])
        elif etype == EventType.DIFFERENTIALS_SET:
            proj.differentials = data["value"]
        elif etype == EventType.DIFFERENTIALS_EVALUATED:
            _append(proj, data["message_id"], "lab_tutor", data["text"])
        elif etype == EventType.INTERP_TEXT_SET:
            proj.interp_text = data["value"]
        elif etype == EventType.INTERPRETATION_EVALUATED:
            _append(
                proj,
                data["interp_note_message_id"],
                "lab_note",
                data["interp_note_text"],
            )
            if data["error"]:
                _append(proj, data["result_message_id"], "lab_note", data["result"])
                proj.interp_result = data["result"]
            else:
                _append(proj, data["result_message_id"], "lab_tutor", data["result"])
                proj.interp_result = data["result"]
        elif etype == EventType.INTERPRETATION_RESET:
            proj.interp_text = ""
            proj.interp_result = ""
        elif etype == EventType.FINAL_ANSWER_FIELD_SET:
            setattr(proj.final_answer, data["field_name"], data["value"])
        elif etype == EventType.FINAL_ANSWER_SUBMITTED:
            _append(proj, data["message_id"], "student", data["ans_text"])
        elif etype == EventType.FEEDBACK_GENERATED:
            proj.feedback = data["feedback"]
        elif etype == EventType.HINT_REQUESTED:
            proj.hints_used += 1
        elif etype == EventType.REFLECTION_ANSWERED:
            proj.reflection_answers.append({"q": data["q"], "a": data["a"]})
        elif etype == EventType.REFLECTION_STEP_ADVANCED:
            proj.reflection_step = data["to_step"]
        elif etype == EventType.REFLECTION_SUMMARIZED:
            _append(proj, data["message_id"], "tutor", data["text"])
        elif etype == EventType.MODE_CHANGED:
            proj.mode = data["to_mode"]
        elif etype == EventType.TUTOR_PROMPT_APPENDED:
            _append(proj, data["message_id"], data["channel"], data["text"])

    return proj
