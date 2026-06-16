from __future__ import annotations

import itertools
import json
import random
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from app.content.cases import get_case
from app.llm.client import LLMClient
from app.schemas.case import Case
from app.services.case_engine import (
    detect_tests_in_message,
    find_lab_result,
    format_lab_result,
    is_test_order,
)
from app.services.prompts import (
    HINT_FALLBACK,
    REFLECTION_QS,
    build_hint_context,
    build_hint_system_prompt,
    build_reflection_summary_prompt,
    make_differential_eval_prompt,
    make_feedback_prompt,
    make_interpretation_eval_prompt,
    make_summary_eval_prompt,
)

Mode = Literal["practice", "exam", "reflection"]
MessageType = Literal[
    "parent", "tutor", "student", "system", "lab", "lab_note", "lab_tutor"
]

OPENING_TEMPLATE = (
    "📍 Immunology Department — Outpatient Clinic\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "{opening_clinical}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "The parent is present and willing to speak with you. You may begin taking history.\n\n"
    "📌 Use the tabs at the top to navigate:\n"
    "  • 💬 Consultation — ask the parent questions and receive examination findings\n"
    "  • 🔬 Investigations — switch here to order tests and view results\n"
    "  • 📋 Final Diagnosis — submit your diagnosis and management plan when ready"
)

SCID_PARENT_WORRY = (
    "Doctor, I am getting worried — he seems more tired today and has developed a "
    "fever again. The rash is spreading. Is it safe for us to go home?"
)
SCID_TUTOR_NOTE = (
    "🟡 Clinical reasoning note: This may be a time-sensitive situation. Some "
    "immunodeficiencies require urgent management before the final genetic diagnosis "
    "is confirmed. What immediate steps are needed — regarding isolation, vaccination "
    "history, and referral?"
)
SCID_URGENT_PATTERN = re.compile(
    r"isolat|live.vacc|urgent|referral|prophylaxis|contact precaution"
)

GENETIC_RESULT_PATTERN = re.compile(r"gene panel|genetic|exome|sequencing", re.IGNORECASE)
GENETIC_LAB_TUTOR_NUDGE = (
    "💡 Clinical reasoning note: Genetic testing has been ordered. It is good practice "
    "to first characterise the immunological phenotype with basic immune tests before "
    "interpreting genetic findings. Are the basic immune results consistent with the "
    "genetic result?"
)

INVESTIGATIONS_ORDERED_NOTE = (
    "🔬 Investigations ordered — switch to the Investigations tab to see results."
)
ALREADY_ORDERED_NOTE = "These investigations have already been ordered."

PROACTIVE_EXAM_NUDGE = (
    "💡 Clinical reasoning note: You have gathered some initial history. Consider "
    "whether a physical examination would add useful information at this point — you "
    "can request one at any time."
)
PARENT_CONNECTION_ERROR = "⚠ Connection error. Please try again."

EXAM_STUDENT_MSG = "I would like to perform a physical examination."
EXAM_PATHOGNOMONIC_NOTE = (
    "💡 Consider what the examination findings add to your differential diagnosis. "
    "Are there any pathognomonic signs?"
)

INTERP_CONNECTION_ERROR = "⚠ Connection error. Please try again."
FEEDBACK_ERROR = "⚠ Could not generate structured feedback. Please try again."

ORDER_PHASES = ("history", "summary", "examination", "differential")


def _default_id_factory() -> Callable[[], str]:
    counter = itertools.count(1)

    def factory() -> str:
        return f"msg-{next(counter)}"

    return factory


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
class Session:
    id: str
    case_id: str
    mode: Mode
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


@dataclass
class SendResult:
    branch: Literal["scid", "tests", "parent"]
    system: str | None = None
    messages: list[dict] | None = None
    max_tokens: int | None = None


class SessionService:
    def __init__(
        self,
        llm: LLMClient,
        rng: Callable[[], float] = random.random,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._llm = llm
        self._rng = rng
        self._id_factory = id_factory or _default_id_factory()
        self._sessions: dict[str, Session] = {}

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def _case(self, session: Session) -> Case:
        case = get_case(session.case_id)
        if case is None:
            raise KeyError(session.case_id)
        return case

    def _add_msg(self, session: Session, text: str, type: MessageType) -> Message:
        message = Message(id=self._id_factory(), type=type, text=text)
        session.messages.append(message)
        return message

    def start_case(self, case_id: str, mode: Mode) -> Session:
        case = get_case(case_id)
        if case is None:
            raise KeyError(case_id)
        session = Session(id=str(uuid.uuid4()), case_id=case_id, mode=mode)
        self._sessions[session.id] = session
        self._add_msg(
            session,
            OPENING_TEMPLATE.format(opening_clinical=case.opening_clinical),
            "system",
        )
        return session

    def send_message(self, session: Session, text: str) -> SendResult:
        case = self._case(session)
        prior_messages = list(session.messages)
        self._add_msg(session, text, "student")

        if (
            session.case_id == "scid"
            and session.phase == "history"
            and len(prior_messages) > 8
        ):
            has_urgent = any(
                SCID_URGENT_PATTERN.search(m.text.lower()) for m in prior_messages
            )
            if not has_urgent and self._rng() > 0.6:
                self._add_msg(session, SCID_PARENT_WORRY, "parent")
                self._add_msg(session, SCID_TUTOR_NOTE, "tutor")
                return SendResult(branch="scid")

        if is_test_order(text):
            detected_keys = detect_tests_in_message(text)
            any_new = False

            if session.phase in ORDER_PHASES:
                session.phase = "tests"

            for key in detected_keys:
                if key in session.ordered_tests:
                    continue
                any_new = True
                session.ordered_tests.add(key)
                result = find_lab_result(case.lab_data, key)
                if result is not None:
                    is_genetic = bool(GENETIC_RESULT_PATTERN.search(result[0]))
                    self._add_msg(
                        session, format_lab_result(result[0], result[1]), "lab"
                    )
                    if (
                        is_genetic
                        and len(session.ordered_tests) < 4
                        and session.mode == "practice"
                    ):
                        self._add_msg(session, GENETIC_LAB_TUTOR_NUDGE, "lab_tutor")
                else:
                    self._add_msg(
                        session, f"📋 {key}: Results not yet available.", "system"
                    )

            if any_new:
                self._add_msg(session, INVESTIGATIONS_ORDERED_NOTE, "system")
            else:
                self._add_msg(session, ALREADY_ORDERED_NOTE, "system")

            return SendResult(branch="tests")

        history = [
            {
                "role": "user" if m.type == "student" else "assistant",
                "content": "[Lab result shown]" if m.type == "lab" else m.text,
            }
            for m in prior_messages[-12:]
        ]
        history.append({"role": "user", "content": text})
        return SendResult(
            branch="parent",
            system=case.parent_prompt,
            messages=history,
            max_tokens=300,
        )

    def append_parent_reply(self, session: Session, text: str) -> None:
        self._add_msg(session, text, "parent")
        parent_count = len([m for m in session.messages if m.type == "parent"])
        if (
            session.mode == "practice"
            and session.phase == "history"
            and not session.exam_done
            and parent_count == 5
        ):
            self._add_msg(session, PROACTIVE_EXAM_NUDGE, "tutor")

    def request_exam(self, session: Session) -> None:
        case = self._case(session)
        self._add_msg(session, EXAM_STUDENT_MSG, "student")
        self._add_msg(
            session,
            f"📋 Physical examination findings:\n\n{case.exam_findings}",
            "system",
        )
        session.exam_done = True
        if session.mode == "practice":
            self._add_msg(session, EXAM_PATHOGNOMONIC_NOTE, "tutor")

    def send_test_order(self, session: Session, text: str) -> None:
        case = self._case(session)
        detected_keys = detect_tests_in_message(text)

        if not detected_keys:
            self._add_msg(
                session,
                f'⚠ "{text}" was not recognised. Try a name like "CBC", '
                '"immunoglobulins", "chest X-ray", or "flow cytometry".',
                "lab_note",
            )
            return

        if session.phase in ORDER_PHASES:
            session.phase = "tests"

        any_new = False
        for key in detected_keys:
            if key in session.ordered_tests:
                continue
            any_new = True
            session.ordered_tests.add(key)
            result = find_lab_result(case.lab_data, key)
            if result is not None:
                is_genetic = bool(GENETIC_RESULT_PATTERN.search(result[0]))
                self._add_msg(session, format_lab_result(result[0], result[1]), "lab")
                if (
                    is_genetic
                    and len(session.ordered_tests) < 4
                    and session.mode == "practice"
                ):
                    self._add_msg(session, GENETIC_LAB_TUTOR_NUDGE, "lab_tutor")
            else:
                self._add_msg(
                    session,
                    f"📋 {key}: Results not yet available for this case.",
                    "lab_note",
                )

        if not any_new:
            self._add_msg(session, ALREADY_ORDERED_NOTE, "lab_note")

    async def submit_summary(self, session: Session) -> None:
        case = self._case(session)
        self._add_msg(session, f"📝 Clinical summary:\n{session.summary}", "student")
        system = make_summary_eval_prompt(case, session.mode)
        feedback = await self._llm.generate(
            system, [{"role": "user", "content": session.summary}], 300
        )
        self._add_msg(session, f"💡 Clinical reasoning note:\n{feedback}", "tutor")
        session.phase = "examination"

    async def submit_differentials(self, session: Session) -> None:
        case = self._case(session)
        self._add_msg(
            session, f"📋 My differential diagnoses:\n{session.differentials}", "student"
        )
        lowered = session.differentials.lower()
        wrong_key = next(
            (k for k in case.wrong_paths.keys() if k in lowered), None
        )
        if wrong_key is not None:
            feedback_text = (
                f"💡 Clinical reasoning note:\n{case.wrong_paths[wrong_key]}"
            )
        else:
            system = make_differential_eval_prompt(case, session.mode)
            reply = await self._llm.generate(
                system, [{"role": "user", "content": session.differentials}], 250
            )
            feedback_text = f"💡 Clinical reasoning note:\n{reply}"
        self._add_msg(session, feedback_text, "lab_tutor")
        session.phase = "tests"

    async def submit_interpretation(self, session: Session) -> None:
        case = self._case(session)
        self._add_msg(session, f"📊 My interpretation:\n{session.interp_text}", "lab_note")
        system = make_interpretation_eval_prompt(case, session.mode)
        try:
            feedback = await self._llm.generate(
                system, [{"role": "user", "content": session.interp_text}], 300
            )
            self._add_msg(session, feedback, "lab_tutor")
            session.interp_result = feedback
        except Exception:
            self._add_msg(session, INTERP_CONNECTION_ERROR, "lab_note")
            session.interp_result = INTERP_CONNECTION_ERROR

    async def submit_final_answer(self, session: Session) -> None:
        case = self._case(session)
        answer = session.final_answer
        ans_text = (
            f"Diagnosis: {answer.diagnosis}\n"
            f"Supporting findings: {answer.findings}\n"
            f"Differentials: {answer.differentials}\n"
            f"Additional tests: {answer.tests}\n"
            f"Management: {answer.management}\n"
            f"Genetic counselling: {answer.genetics}\n"
            f"Explanation to parent: {answer.explanation}"
        )
        self._add_msg(session, f"✅ Final answer submitted:\n{ans_text}", "student")
        system = f"{make_feedback_prompt(case)}\n\nStudent's final answer:\n{ans_text}"
        try:
            raw_feedback = await self._llm.generate(
                system, [{"role": "user", "content": ans_text}], 1500
            )
            match = re.search(r"\{[\s\S]*\}", raw_feedback)
            parsed = json.loads(match.group(0) if match else raw_feedback.strip())
            session.feedback = parsed
            session.phase = "feedback"
        except Exception:
            self._add_msg(session, FEEDBACK_ERROR, "system")

    async def request_hint(self, session: Session) -> str:
        case = self._case(session)
        session.hints_used += 1
        msgs = [{"text": m.text, "type": m.type} for m in session.messages]
        built = build_hint_context(
            case,
            session.phase,
            msgs,
            list(session.ordered_tests),
            session.hints_used,
        )
        system = build_hint_system_prompt(built["context"])
        try:
            return await self._llm.generate(
                system, [{"role": "user", "content": "I need a hint."}], 200
            )
        except Exception:
            return HINT_FALLBACK

    async def submit_reflection(self, session: Session, text: str) -> None:
        case = self._case(session)
        session.reflection_answers.append(
            {"q": REFLECTION_QS[session.reflection_step], "a": text}
        )
        if session.reflection_step < len(REFLECTION_QS) - 1:
            session.reflection_step += 1
            return
        system = build_reflection_summary_prompt(case)
        refl_text = "\n\n".join(
            f"Q: {r['q']}\nA: {r['a']}" for r in session.reflection_answers
        )
        summary = await self._llm.generate(
            system, [{"role": "user", "content": refl_text}], 300
        )
        self._add_msg(session, summary, "tutor")

    def go_to_summary(self, session: Session, prompt: str) -> None:
        session.phase = "summary"
        self._add_msg(session, prompt, "tutor")

    def go_to_differential(self, session: Session, prompt: str) -> None:
        session.phase = "differential"
        self._add_msg(session, prompt, "tutor")

    def go_to_interpretation(self, session: Session, prompt: str) -> None:
        session.phase = "interpretation"
        self._add_msg(session, prompt, "lab_tutor")

    def go_to_final(self, session: Session, prompt: str) -> None:
        session.phase = "final"
        self._add_msg(session, prompt, "tutor")

    def go_to_tests(self, session: Session) -> None:
        session.interp_text = ""
        session.interp_result = ""
        session.phase = "tests"

    def go_to_reflection(self, session: Session) -> None:
        session.mode = "reflection"
        session.phase = "reflection"

    def set_summary(self, session: Session, value: str) -> None:
        session.summary = value

    def set_differentials(self, session: Session, value: str) -> None:
        session.differentials = value

    def set_interp_text(self, session: Session, value: str) -> None:
        session.interp_text = value

    def set_final_answer_field(self, session: Session, field_name: str, value: str) -> None:
        setattr(session.final_answer, field_name, value)
