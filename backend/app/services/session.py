from __future__ import annotations

import random
import re
import uuid
from collections.abc import Callable

from app.core.config import get_settings
from app.llm.client import LLMClient
from app.schemas.case import Case
from app.services.case_engine import (
    detect_tests_in_message,
    find_lab_result,
    format_lab_result,
)
from app.services.projection import (
    AttemptProjection,
    EventType,
    FinalAnswer,
    Message,
    MessageType,
    Mode,
    NewEvent,
    SendResult,
    fold,
)
from app.services.prompts import (
    FEEDBACK_SCHEMA,
    REFLECTION_QS,
    build_hint_context,
    build_hint_system_prompt,
    build_reflection_summary_prompt,
    hint_fallback,
    language_directive,
    make_differential_eval_prompt,
    make_feedback_prompt,
    make_interpretation_eval_prompt,
    make_summary_eval_prompt,
)
from app.services.routing import (
    ExamAction,
    HeuristicRouter,
    TestOrderAction,
    ToolUseRouter,
    select_router,
)
from app.services.stores import (
    AttemptStore,
    CaseSource,
    InMemoryAttemptStore,
    RegistryCaseSource,
)

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

EXAM_PATHOGNOMONIC_NOTE = (
    "💡 Consider what the examination findings add to your differential diagnosis. "
    "Are there any pathognomonic signs?"
)

INTERP_CONNECTION_ERROR = "⚠ Connection error. Please try again."
FEEDBACK_ERROR = "⚠ Could not generate structured feedback. Please try again."

ORDER_PHASES = ("history", "summary", "examination", "differential")


def _default_id_factory() -> Callable[[], str]:
    def factory() -> str:
        return f"msg-{uuid.uuid4().hex}"

    return factory


class SessionService:
    def __init__(
        self,
        llm: LLMClient,
        store: AttemptStore | None = None,
        cases: CaseSource | None = None,
        rng: Callable[[], float] = random.random,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._llm = llm
        self._store = store or InMemoryAttemptStore()
        self._cases = cases or RegistryCaseSource()
        self._rng = rng
        self._id_factory = id_factory or _default_id_factory()
        self._heuristic_router = HeuristicRouter()
        self._tool_router = ToolUseRouter(llm)

    def _next_id(self) -> str:
        return self._id_factory()

    async def _case(self, proj: AttemptProjection) -> Case:
        case = await self._cases.get_case(proj.case_id, proj.language)
        if case is None:
            raise KeyError(proj.case_id)
        return case

    async def _load(self, attempt_id: str) -> AttemptProjection | None:
        events = await self._store.load_events(attempt_id)
        if not events:
            return None
        return fold(events)

    async def _require(self, attempt_id: str) -> AttemptProjection:
        proj = await self._load(attempt_id)
        if proj is None:
            raise ValueError(f"Unknown session: {attempt_id}")
        return proj

    async def _commit(
        self,
        attempt_id: str,
        events: list[NewEvent],
        base: AttemptProjection | None = None,
    ) -> AttemptProjection:
        persisted = await self._store.append_events(attempt_id, events)
        if base is not None:
            proj = fold(persisted, base=base)
        else:
            proj = fold(await self._store.load_events(attempt_id))
        await self._store.sync_projection(attempt_id, proj)
        return proj

    async def get(self, attempt_id: str) -> AttemptProjection | None:
        return await self._load(attempt_id)

    async def get_attempt_owner(self, attempt_id: str) -> str | None:
        return await self._store.get_attempt_owner(attempt_id)

    async def get_attempt_meta(self, attempt_id: str):
        return await self._store.get_attempt_meta(attempt_id)

    async def events(self, attempt_id: str):
        return await self._store.load_events(attempt_id)

    async def events_many(self, attempt_ids: list[str]):
        return await self._store.load_events_many(attempt_ids)

    async def get_case(self, case_id: str, language: str = "en") -> Case | None:
        return await self._cases.get_case(case_id, language)

    async def start_case(
        self,
        case_id: str,
        mode: Mode,
        student_id: str | None = None,
        language: str = "en",
        assignment_id: str | None = None,
    ) -> AttemptProjection:
        if language not in ("en", "lv"):
            raise ValueError(f"Unsupported language: {language}")
        case = await self._cases.get_case(case_id, language)
        if case is None:
            raise KeyError(case_id)
        attempt_id = await self._store.create_attempt(
            case_id, mode, language, student_id, assignment_id
        )
        events = [
            NewEvent(
                type=EventType.SESSION_STARTED,
                data={
                    "id": attempt_id,
                    "case_slug": case_id,
                    "mode": mode,
                    "language": language,
                },
            ),
            NewEvent(
                type=EventType.SYSTEM_MESSAGE_APPENDED,
                data={
                    "message_id": self._next_id(),
                    "text": OPENING_TEMPLATE.format(
                        opening_clinical=case.opening_clinical
                    ),
                },
            ),
        ]
        return await self._commit(attempt_id, events)

    def _apply_test_order(
        self,
        events: list[NewEvent],
        proj: AttemptProjection,
        case: Case,
        keys: list[str],
        *,
        unavailable_channel: str,
        unavailable_text: Callable[[str], str],
        always_batch_note: bool,
    ) -> None:
        ordered = set(proj.ordered_tests)
        any_new = False

        if proj.phase in ORDER_PHASES:
            events.append(
                NewEvent(
                    type=EventType.PHASE_CHANGED,
                    data={"from_phase": proj.phase, "to_phase": "tests"},
                )
            )

        for key in keys:
            if key in ordered:
                continue
            any_new = True
            ordered.add(key)
            events.append(NewEvent(type=EventType.TEST_ORDERED, data={"key": key}))
            result = find_lab_result(case.lab_data, key)
            if result is not None:
                is_genetic = bool(GENETIC_RESULT_PATTERN.search(result[0]))
                events.append(
                    NewEvent(
                        type=EventType.LAB_RESULT_SHOWN,
                        data={
                            "message_id": self._next_id(),
                            "text": format_lab_result(result[0], result[1]),
                            "key": key,
                            "is_genetic": is_genetic,
                        },
                    )
                )
                if is_genetic and len(ordered) < 4 and proj.mode == "practice":
                    events.append(
                        NewEvent(
                            type=EventType.GENETIC_NUDGE_SHOWN,
                            data={
                                "message_id": self._next_id(),
                                "text": GENETIC_LAB_TUTOR_NUDGE,
                            },
                        )
                    )
            else:
                events.append(
                    NewEvent(
                        type=EventType.TEST_UNAVAILABLE_NOTED,
                        data={
                            "message_id": self._next_id(),
                            "text": unavailable_text(key),
                            "key": key,
                            "channel": unavailable_channel,
                        },
                    )
                )

        if always_batch_note or not any_new:
            note_text = (
                INVESTIGATIONS_ORDERED_NOTE if any_new else ALREADY_ORDERED_NOTE
            )
            events.append(
                NewEvent(
                    type=EventType.ORDER_BATCH_NOTED,
                    data={
                        "message_id": self._next_id(),
                        "text": note_text,
                        "any_new": any_new,
                        "channel": unavailable_channel,
                    },
                )
            )

    def _apply_parent(
        self,
        events: list[NewEvent],
        proj: AttemptProjection,
        case: Case,
        prior_messages: list[Message],
        text: str,
    ) -> SendResult:
        directive = language_directive(proj.language)
        parent_system = (
            f"{case.parent_prompt}\n\n{directive}"
            if directive
            else case.parent_prompt
        )
        dialogue = [
            m for m in prior_messages if m.type in ("student", "parent", "lab")
        ]
        history = [
            {
                "role": "user" if m.type == "student" else "assistant",
                "content": "[Lab result shown]" if m.type == "lab" else m.text,
            }
            for m in dialogue[-12:]
        ]
        history.append({"role": "user", "content": text})
        events.append(
            NewEvent(
                type=EventType.PARENT_REPLY_REQUESTED,
                data={
                    "system": parent_system,
                    "history": history,
                    "max_tokens": 300,
                },
            )
        )
        return SendResult(
            branch="parent",
            system=parent_system,
            messages=history,
            max_tokens=300,
        )

    async def send_message(
        self, attempt_id: str, text: str
    ) -> tuple[SendResult, AttemptProjection]:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        prior_messages = list(proj.messages)

        events: list[NewEvent] = [
            NewEvent(
                type=EventType.STUDENT_MESSAGE_SENT,
                data={"message_id": self._next_id(), "text": text},
            )
        ]

        if (
            proj.case_id == "scid"
            and proj.phase == "history"
            and len(prior_messages) > 8
        ):
            has_urgent = any(
                SCID_URGENT_PATTERN.search(m.text.lower()) for m in prior_messages
            )
            if not has_urgent:
                rng_draw = self._rng()
                if rng_draw > 0.6:
                    events.append(
                        NewEvent(
                            type=EventType.SCID_NUDGE_FIRED,
                            data={
                                "rng_draw": rng_draw,
                                "parent_message_id": self._next_id(),
                                "parent_text": SCID_PARENT_WORRY,
                                "tutor_message_id": self._next_id(),
                                "tutor_text": SCID_TUTOR_NOTE,
                            },
                        )
                    )
                    new_proj = await self._commit(attempt_id, events, base=proj)
                    return SendResult(branch="scid"), new_proj

        router = select_router(
            get_settings().CASEROOM_ROUTING,
            proj.language,
            self._heuristic_router,
            self._tool_router,
        )
        action = await router.route(proj, case, text)

        if isinstance(action, TestOrderAction):
            self._apply_test_order(
                events,
                proj,
                case,
                action.keys,
                unavailable_channel="system",
                unavailable_text=lambda key: f"📋 {key}: Results not yet available.",
                always_batch_note=True,
            )
            new_proj = await self._commit(attempt_id, events, base=proj)
            return SendResult(branch="tests"), new_proj

        if isinstance(action, ExamAction):
            self._append_exam(events, case, proj)
            new_proj = await self._commit(attempt_id, events, base=proj)
            return SendResult(branch="tests"), new_proj

        result = self._apply_parent(events, proj, case, prior_messages, text)
        new_proj = await self._commit(attempt_id, events, base=proj)
        new_proj.pending_parent = result
        return result, new_proj

    async def append_parent_reply(
        self, attempt_id: str, text: str
    ) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events: list[NewEvent] = [
            NewEvent(
                type=EventType.PARENT_REPLY_APPENDED,
                data={"message_id": self._next_id(), "text": text},
            )
        ]
        parent_count = len([m for m in proj.messages if m.type == "parent"]) + 1
        if (
            proj.mode == "practice"
            and proj.phase == "history"
            and not proj.exam_done
            and parent_count == 5
        ):
            events.append(
                NewEvent(
                    type=EventType.EXAM_NUDGE_SHOWN,
                    data={
                        "message_id": self._next_id(),
                        "text": PROACTIVE_EXAM_NUDGE,
                    },
                )
            )
        return await self._commit(attempt_id, events, base=proj)

    def _append_exam(
        self, events: list[NewEvent], case: Case, proj: AttemptProjection
    ) -> None:
        exam_text = f"📋 Physical examination findings:\n\n{case.exam_findings}"
        events.append(
            NewEvent(
                type=EventType.EXAM_PERFORMED,
                data={
                    "student_message_id": self._next_id(),
                    "exam_message_id": self._next_id(),
                    "exam_text": exam_text,
                },
            )
        )
        if proj.mode == "practice":
            events.append(
                NewEvent(
                    type=EventType.EXAM_PATHOGNOMONIC_NOTED,
                    data={
                        "message_id": self._next_id(),
                        "text": EXAM_PATHOGNOMONIC_NOTE,
                    },
                )
            )

    async def request_exam(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        events: list[NewEvent] = []
        self._append_exam(events, case, proj)
        return await self._commit(attempt_id, events, base=proj)

    async def send_test_order(self, attempt_id: str, text: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        detected_keys = detect_tests_in_message(text)

        if not detected_keys:
            events = [
                NewEvent(
                    type=EventType.TEST_ORDER_UNRECOGNIZED,
                    data={
                        "message_id": self._next_id(),
                        "text": (
                            f'⚠ "{text}" was not recognised. Try a name like "CBC", '
                            '"immunoglobulins", "chest X-ray", or "flow cytometry".'
                        ),
                    },
                )
            ]
            return await self._commit(attempt_id, events, base=proj)

        events = []
        self._apply_test_order(
            events,
            proj,
            case,
            detected_keys,
            unavailable_channel="lab_note",
            unavailable_text=lambda key: (
                f"📋 {key}: Results not yet available for this case."
            ),
            always_batch_note=False,
        )
        return await self._commit(attempt_id, events, base=proj)

    async def submit_summary(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        events: list[NewEvent] = [
            NewEvent(
                type=EventType.STUDENT_MESSAGE_SENT,
                data={
                    "message_id": self._next_id(),
                    "text": f"📝 Clinical summary:\n{proj.summary}",
                },
            )
        ]
        system = make_summary_eval_prompt(case, proj.mode, proj.language)
        feedback = await self._llm.generate(
            system, [{"role": "user", "content": proj.summary}], 300
        )
        events.append(
            NewEvent(
                type=EventType.SUMMARY_EVALUATED,
                data={
                    "tutor_message_id": self._next_id(),
                    "tutor_text": f"💡 Clinical reasoning note:\n{feedback}",
                    "feedback": feedback,
                },
            )
        )
        events.append(
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "examination"},
            )
        )
        return await self._commit(attempt_id, events, base=proj)

    async def submit_differentials(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        events: list[NewEvent] = [
            NewEvent(
                type=EventType.STUDENT_MESSAGE_SENT,
                data={
                    "message_id": self._next_id(),
                    "text": f"📋 My differential diagnoses:\n{proj.differentials}",
                },
            )
        ]
        lowered = proj.differentials.lower()
        wrong_key = next(
            (k for k in case.wrong_paths.keys() if k in lowered), None
        )
        if wrong_key is not None:
            feedback_text = (
                f"💡 Clinical reasoning note:\n{case.wrong_paths[wrong_key]}"
            )
            source = "wrong_path"
        else:
            system = make_differential_eval_prompt(case, proj.mode, proj.language)
            reply = await self._llm.generate(
                system, [{"role": "user", "content": proj.differentials}], 250
            )
            feedback_text = f"💡 Clinical reasoning note:\n{reply}"
            source = "llm"
        data = {
            "message_id": self._next_id(),
            "text": feedback_text,
            "source": source,
        }
        if wrong_key is not None:
            data["wrong_key"] = wrong_key
        events.append(
            NewEvent(type=EventType.DIFFERENTIALS_EVALUATED, data=data)
        )
        events.append(
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "tests"},
            )
        )
        return await self._commit(attempt_id, events, base=proj)

    async def submit_interpretation(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        interp_note_message_id = self._next_id()
        interp_note_text = f"📊 My interpretation:\n{proj.interp_text}"
        system = make_interpretation_eval_prompt(case, proj.mode, proj.language)
        try:
            feedback = await self._llm.generate(
                system, [{"role": "user", "content": proj.interp_text}], 300
            )
            data = {
                "interp_note_message_id": interp_note_message_id,
                "interp_note_text": interp_note_text,
                "result_message_id": self._next_id(),
                "result": feedback,
                "error": False,
            }
        except Exception:
            data = {
                "interp_note_message_id": interp_note_message_id,
                "interp_note_text": interp_note_text,
                "result_message_id": self._next_id(),
                "result": INTERP_CONNECTION_ERROR,
                "error": True,
            }
        events = [NewEvent(type=EventType.INTERPRETATION_EVALUATED, data=data)]
        return await self._commit(attempt_id, events, base=proj)

    async def submit_final_answer(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        answer = proj.final_answer
        ans_text = (
            f"Diagnosis: {answer.diagnosis}\n"
            f"Supporting findings: {answer.findings}\n"
            f"Differentials: {answer.differentials}\n"
            f"Additional tests: {answer.tests}\n"
            f"Management: {answer.management}\n"
            f"Genetic counselling: {answer.genetics}\n"
            f"Explanation to parent: {answer.explanation}"
        )
        events: list[NewEvent] = [
            NewEvent(
                type=EventType.FINAL_ANSWER_SUBMITTED,
                data={
                    "message_id": self._next_id(),
                    "ans_text": f"✅ Final answer submitted:\n{ans_text}",
                },
            )
        ]
        system = (
            f"{make_feedback_prompt(case, proj.language)}"
            f"\n\nStudent's final answer:\n{ans_text}"
        )
        try:
            parsed = await self._llm.generate_structured(
                system, [{"role": "user", "content": ans_text}], FEEDBACK_SCHEMA, 1500
            )
            events.append(
                NewEvent(
                    type=EventType.FEEDBACK_GENERATED, data={"feedback": parsed}
                )
            )
            events.append(
                NewEvent(
                    type=EventType.PHASE_CHANGED,
                    data={"from_phase": proj.phase, "to_phase": "feedback"},
                )
            )
        except Exception:
            events.append(
                NewEvent(
                    type=EventType.SYSTEM_MESSAGE_APPENDED,
                    data={"message_id": self._next_id(), "text": FEEDBACK_ERROR},
                )
            )
        return await self._commit(attempt_id, events, base=proj)

    async def request_hint(self, attempt_id: str) -> str:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        hints_used = proj.hints_used + 1
        msgs = [{"text": m.text, "type": m.type} for m in proj.messages]
        built = build_hint_context(
            case,
            proj.phase,
            msgs,
            list(proj.ordered_tests),
            hints_used,
        )
        system = build_hint_system_prompt(built["context"], proj.language)
        try:
            hint_text = await self._llm.generate(
                system, [{"role": "user", "content": "I need a hint."}], 200
            )
        except Exception:
            hint_text = hint_fallback(proj.language)
        await self._commit(
            attempt_id,
            [NewEvent(type=EventType.HINT_REQUESTED, data={"hint_text": hint_text})],
            base=proj,
        )
        return hint_text

    async def submit_reflection(self, attempt_id: str, text: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        case = await self._case(proj)
        events: list[NewEvent] = [
            NewEvent(
                type=EventType.REFLECTION_ANSWERED,
                data={
                    "step": proj.reflection_step,
                    "q": REFLECTION_QS[proj.reflection_step],
                    "a": text,
                },
            )
        ]
        if proj.reflection_step < len(REFLECTION_QS) - 1:
            events.append(
                NewEvent(
                    type=EventType.REFLECTION_STEP_ADVANCED,
                    data={"to_step": proj.reflection_step + 1},
                )
            )
            return await self._commit(attempt_id, events, base=proj)

        system = build_reflection_summary_prompt(case, proj.language)
        answers = [{"q": r["q"], "a": r["a"]} for r in proj.reflection_answers]
        answers.append({"q": REFLECTION_QS[proj.reflection_step], "a": text})
        refl_text = "\n\n".join(f"Q: {r['q']}\nA: {r['a']}" for r in answers)
        summary = await self._llm.generate(
            system, [{"role": "user", "content": refl_text}], 300
        )
        events.append(
            NewEvent(
                type=EventType.REFLECTION_SUMMARIZED,
                data={"message_id": self._next_id(), "text": summary},
            )
        )
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_summary(self, attempt_id: str, prompt: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "summary"},
            ),
            NewEvent(
                type=EventType.TUTOR_PROMPT_APPENDED,
                data={
                    "message_id": self._next_id(),
                    "text": prompt,
                    "channel": "tutor",
                },
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_differential(
        self, attempt_id: str, prompt: str
    ) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "differential"},
            ),
            NewEvent(
                type=EventType.TUTOR_PROMPT_APPENDED,
                data={
                    "message_id": self._next_id(),
                    "text": prompt,
                    "channel": "tutor",
                },
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_interpretation(
        self, attempt_id: str, prompt: str
    ) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "interpretation"},
            ),
            NewEvent(
                type=EventType.TUTOR_PROMPT_APPENDED,
                data={
                    "message_id": self._next_id(),
                    "text": prompt,
                    "channel": "lab_tutor",
                },
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_final(self, attempt_id: str, prompt: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "final"},
            ),
            NewEvent(
                type=EventType.TUTOR_PROMPT_APPENDED,
                data={
                    "message_id": self._next_id(),
                    "text": prompt,
                    "channel": "tutor",
                },
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_tests(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(type=EventType.INTERPRETATION_RESET, data={}),
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "tests"},
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def go_to_reflection(self, attempt_id: str) -> AttemptProjection:
        proj = await self._require(attempt_id)
        events = [
            NewEvent(
                type=EventType.MODE_CHANGED,
                data={"from_mode": proj.mode, "to_mode": "reflection"},
            ),
            NewEvent(
                type=EventType.PHASE_CHANGED,
                data={"from_phase": proj.phase, "to_phase": "reflection"},
            ),
        ]
        return await self._commit(attempt_id, events, base=proj)

    async def set_summary(self, attempt_id: str, value: str) -> AttemptProjection:
        return await self._commit(
            attempt_id,
            [NewEvent(type=EventType.SUMMARY_SET, data={"value": value})],
        )

    async def set_differentials(self, attempt_id: str, value: str) -> AttemptProjection:
        return await self._commit(
            attempt_id,
            [NewEvent(type=EventType.DIFFERENTIALS_SET, data={"value": value})],
        )

    async def set_interp_text(self, attempt_id: str, value: str) -> AttemptProjection:
        return await self._commit(
            attempt_id,
            [NewEvent(type=EventType.INTERP_TEXT_SET, data={"value": value})],
        )

    async def set_final_answer_fields(
        self, attempt_id: str, values: dict[str, str]
    ) -> AttemptProjection:
        events = [
            NewEvent(
                type=EventType.FINAL_ANSWER_FIELD_SET,
                data={"field_name": field_name, "value": value},
            )
            for field_name, value in values.items()
        ]
        return await self._commit(attempt_id, events)

    async def set_final_answer_field(
        self, attempt_id: str, field_name: str, value: str
    ) -> AttemptProjection:
        return await self._commit(
            attempt_id,
            [
                NewEvent(
                    type=EventType.FINAL_ANSWER_FIELD_SET,
                    data={"field_name": field_name, "value": value},
                )
            ],
        )


__all__ = [
    "AttemptProjection",
    "FinalAnswer",
    "Message",
    "MessageType",
    "Mode",
    "SendResult",
    "SessionService",
]
