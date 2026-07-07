from __future__ import annotations

import itertools

import pytest

import app.content.cases as cases_module
from app.content.cases import XLA
from app.schemas.case import Case
from app.services import SessionService
from app.services.projection import EventType, NewEvent
from app.services.prompts import (
    FEEDBACK_SCHEMA,
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


FEEDBACK_FIXTURE = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "XLA is correct.",
    "wellDone": ["Recognised absent B cells"],
    "missing": ["Could have screened earlier"],
    "keyClues": ["Onset at 6 months"],
    "reasoningPathway": "Recurrent infections, absent B cells, BTK variant.",
    "managementPoints": ["Start IVIG"],
    "geneticPoints": ["X-linked recessive"],
    "revisionTopic": "Recurrent bacterial infection in infancy.",
    "scores": {
        "historyTaking": "Good",
        "examination": "Good",
        "differential": "Excellent",
        "testSelection": "Good",
        "interpretation": "Excellent",
        "management": "Good",
    },
}


class FakeLLMClient:
    def __init__(self, reply="canned-reply", raises=False, structured=None):
        self._reply = reply
        self._raises = raises
        self._structured = structured if structured is not None else FEEDBACK_FIXTURE
        self.calls = []
        self.structured_calls = []

    async def generate(self, system, messages, max_tokens):
        self.calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        if self._raises:
            raise RuntimeError("boom")
        return self._reply

    async def generate_structured(self, system, messages, schema, max_tokens):
        self.structured_calls.append(
            {
                "system": system,
                "messages": messages,
                "schema": schema,
                "max_tokens": max_tokens,
            }
        )
        if self._raises:
            raise RuntimeError("boom")
        return self._structured


def sequential_ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


def make_service(reply="canned-reply", rng=None, raises=False, structured=None):
    llm = FakeLLMClient(reply=reply, raises=raises, structured=structured)
    service = SessionService(
        llm,
        rng=rng or (lambda: 0.0),
        id_factory=sequential_ids(),
    )
    return service, llm


async def append_raw(service, attempt_id, type, data):
    await service._store.append_events(attempt_id, [NewEvent(type=type, data=data)])


async def add_student(service, attempt_id, text):
    await append_raw(
        service,
        attempt_id,
        EventType.STUDENT_MESSAGE_SENT,
        {"message_id": service._next_id(), "text": text},
    )


async def add_message(service, attempt_id, type, text):
    type_to_event = {
        "system": EventType.SYSTEM_MESSAGE_APPENDED,
        "student": EventType.STUDENT_MESSAGE_SENT,
    }
    if type in type_to_event:
        await append_raw(
            service,
            attempt_id,
            type_to_event[type],
            {"message_id": service._next_id(), "text": text},
        )
    elif type == "parent":
        await append_raw(
            service,
            attempt_id,
            EventType.PARENT_REPLY_APPENDED,
            {"message_id": service._next_id(), "text": text},
        )
    elif type == "lab":
        await append_raw(
            service,
            attempt_id,
            EventType.LAB_RESULT_SHOWN,
            {"message_id": service._next_id(), "text": text, "key": "x", "is_genetic": False},
        )
    else:
        raise ValueError(type)


async def set_phase(service, attempt_id, phase):
    proj = await service.get(attempt_id)
    await append_raw(
        service,
        attempt_id,
        EventType.PHASE_CHANGED,
        {"from_phase": proj.phase, "to_phase": phase},
    )


SCID = Case(
    id="scid",
    title="A Baby With Infections After BCG Vaccination",
    topic="SCID",
    patient="Male infant, 2.5 months old",
    difficulty="Advanced",
    opening_clinical="A male infant referred after BCG complications.",
    opening="opening narrative",
    target_diagnosis="SCID — Artemis deficiency",
    target_iuis="Combined immunodeficiency",
    red_flags=["live vaccine given"],
    parent_prompt="You are the parent of an infant with SCID.",
    lab_data={"TREC assay": "TREC undetectable."},
    exam_findings="Failure to thrive.",
    model_diagnosis="SCID",
    model_management="Urgent HSCT.",
    model_genetic_counselling="Autosomal recessive.",
    key_clues=["BCG complications", "absent T cells"],
    wrong_paths={"omenn": "Consider Omenn.", "cvid": "Too early for CVID."},
)


@pytest.fixture
def register_scid():
    cases_module.CASES[SCID.id] = SCID
    yield
    cases_module.CASES.pop(SCID.id, None)


async def test_start_case_resets_and_appends_opening():
    service, llm = make_service()
    session = await service.start_case("xla", "practice")

    assert session.case_id == "xla"
    assert session.mode == "practice"
    assert session.phase == "history"
    assert session.hints_used == 0
    assert session.ordered_tests == set()
    assert session.exam_done is False
    assert session.summary == ""
    assert session.differentials == ""
    assert session.feedback is None
    assert session.reflection_step == 0
    assert session.reflection_answers == []
    assert session.interp_text == ""
    assert session.interp_result == ""
    assert session.final_answer.diagnosis == ""

    assert len(session.messages) == 1
    opening = session.messages[0]
    assert opening.type == "system"
    assert opening.id == "id-1"
    assert XLA.opening_clinical in opening.text
    assert opening.text.startswith("📍 Immunology Department — Outpatient Clinic")
    assert llm.calls == []


async def test_start_case_unknown_case_raises():
    service, _ = make_service()
    with pytest.raises(KeyError):
        await service.start_case("nope", "practice")


async def test_send_message_test_order_branch():
    service, llm = make_service()
    session = await service.start_case("xla", "practice")

    result, session = await service.send_message(
        session.id, "Please order immunoglobulins and a CBC"
    )

    assert result.branch == "tests"
    assert session.phase == "tests"
    assert session.ordered_tests == {"immunoglobulin", "CBC"}
    lab_msgs = [m for m in session.messages if m.type == "lab"]
    assert len(lab_msgs) == 2
    assert lab_msgs[0].text.startswith("__LAB__CBC / full blood count")
    assert lab_msgs[1].text.startswith("__LAB__immunoglobulins")
    assert session.messages[-1].type == "system"
    assert session.messages[-1].text == (
        "🔬 Investigations ordered — switch to the Investigations tab to see results."
    )
    assert llm.calls == []


async def test_send_message_test_order_genetic_nudge_in_practice():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    _, session = await service.send_message(
        session.id, "order the immunodeficiency gene panel"
    )

    assert "immunodeficiency gene panel" in session.ordered_tests
    lab_tutor = [m for m in session.messages if m.type == "lab_tutor"]
    assert len(lab_tutor) == 1
    assert lab_tutor[0].text.startswith("💡 Clinical reasoning note: Genetic testing")


async def test_send_message_test_order_already_ordered():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    _, session = await service.send_message(session.id, "order a CBC")
    before = len(session.messages)

    _, session = await service.send_message(session.id, "order a CBC")

    assert session.messages[-1].text == "These investigations have already been ordered."
    assert len(session.messages) == before + 2


async def _pad_history(service, attempt_id, count):
    for i in range(count):
        await add_student(service, attempt_id, f"filler {i}")


async def test_send_message_scid_trigger_fires_when_rng_above_threshold(register_scid):
    service, llm = make_service(rng=lambda: 0.7)
    session = await service.start_case("scid", "practice")
    await _pad_history(service, session.id, 9)

    result, session = await service.send_message(session.id, "tell me about the rash")

    assert result.branch == "scid"
    assert result.messages is None
    parent = [m for m in session.messages if m.type == "parent"]
    tutor = [m for m in session.messages if m.type == "tutor"]
    assert len(parent) == 1
    assert parent[0].text.startswith("Doctor, I am getting worried")
    assert len(tutor) == 1
    assert tutor[0].text.startswith("🟡 Clinical reasoning note")
    assert llm.calls == []


async def test_send_message_scid_trigger_not_fired_when_rng_at_threshold(register_scid):
    service, _ = make_service(rng=lambda: 0.6)
    session = await service.start_case("scid", "practice")
    await _pad_history(service, session.id, 9)

    result, session = await service.send_message(session.id, "tell me about the rash")

    assert result.branch == "parent"
    assert result.system == SCID.parent_prompt
    assert result.max_tokens == 300
    assert not any(
        m.text.startswith("Doctor, I am getting worried") for m in session.messages
    )


async def test_send_message_scid_trigger_suppressed_by_urgent_keyword(register_scid):
    service, _ = make_service(rng=lambda: 0.99)
    session = await service.start_case("scid", "practice")
    await add_student(service, session.id, "we should arrange urgent isolation")
    await _pad_history(service, session.id, 9)

    result, session = await service.send_message(session.id, "tell me about the rash")

    assert result.branch == "parent"


async def test_send_message_parent_branch_history_mapping():
    service, llm = make_service()
    session = await service.start_case("xla", "practice")
    opening_text = session.messages[0].text
    await add_message(service, session.id, "student", "When did it start?")
    await add_message(service, session.id, "parent", "It started at six months.")
    await add_message(service, session.id, "lab", "__LAB__CBC\nWBC normal")

    result, session = await service.send_message(session.id, "Any family history?")

    assert result.branch == "parent"
    assert result.system == XLA.parent_prompt
    assert result.max_tokens == 300
    assert result.messages == [
        {"role": "user", "content": "When did it start?"},
        {"role": "assistant", "content": "It started at six months."},
        {"role": "assistant", "content": "[Lab result shown]"},
        {"role": "user", "content": "Any family history?"},
    ]
    assert all(m["content"] != opening_text for m in result.messages)
    assert llm.calls == []


async def test_append_parent_reply_emits_nudge_on_fifth_parent_message():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    for _ in range(4):
        session = await service.append_parent_reply(session.id, "reply")
    assert not any(
        m.text.startswith("💡 Clinical reasoning note: You have gathered")
        for m in session.messages
    )

    session = await service.append_parent_reply(session.id, "fifth reply")

    nudges = [
        m
        for m in session.messages
        if m.text.startswith("💡 Clinical reasoning note: You have gathered")
    ]
    assert len(nudges) == 1
    assert nudges[0].type == "tutor"


async def test_append_parent_reply_no_nudge_in_exam_mode():
    service, _ = make_service()
    session = await service.start_case("xla", "exam")
    for _ in range(5):
        session = await service.append_parent_reply(session.id, "reply")
    assert not any(
        m.text.startswith("💡 Clinical reasoning note: You have gathered")
        for m in session.messages
    )


async def test_request_exam_appends_findings_and_practice_note():
    service, llm = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.request_exam(session.id)

    types = [m.type for m in session.messages[-3:]]
    assert types == ["student", "system", "tutor"]
    assert session.messages[-2].text.startswith("📋 Physical examination findings:")
    assert XLA.exam_findings in session.messages[-2].text
    assert session.exam_done is True
    assert session.phase == "history"
    assert llm.calls == []


async def test_request_exam_no_note_in_exam_mode():
    service, _ = make_service()
    session = await service.start_case("xla", "exam")

    session = await service.request_exam(session.id)

    assert session.messages[-1].type == "system"
    assert session.exam_done is True


async def test_send_test_order_not_recognised():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.send_test_order(session.id, "xyzzy nonsense")

    assert session.messages[-1].type == "lab_note"
    assert "was not recognised" in session.messages[-1].text
    assert session.ordered_tests == set()


async def test_send_test_order_phase_jump_and_lab():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.send_test_order(session.id, "immunoglobulins")

    assert session.phase == "tests"
    assert "immunoglobulin" in session.ordered_tests
    assert session.messages[-1].type == "lab"
    assert session.messages[-1].text.startswith("__LAB__immunoglobulins")


async def test_send_test_order_already_ordered_note():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    await service.send_test_order(session.id, "CBC")

    session = await service.send_test_order(session.id, "CBC")

    assert session.messages[-1].type == "lab_note"
    assert session.messages[-1].text == "These investigations have already been ordered."


async def test_submit_summary_calls_llm_and_transitions():
    service, llm = make_service(reply="good summary feedback")
    session = await service.start_case("xla", "practice")
    await service.set_summary(session.id, "My summary text")

    session = await service.submit_summary(session.id)

    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == make_summary_eval_prompt(XLA, "practice")
    assert call["messages"] == [{"role": "user", "content": "My summary text"}]
    assert call["max_tokens"] == 300
    assert session.phase == "examination"
    assert session.messages[-1].type == "tutor"
    assert session.messages[-1].text == "💡 Clinical reasoning note:\ngood summary feedback"


async def test_submit_differentials_wrong_path_shortcut_no_llm():
    service, llm = make_service()
    session = await service.start_case("xla", "practice")
    await service.set_differentials(session.id, "I think this is CVID actually")

    session = await service.submit_differentials(session.id)

    assert llm.calls == []
    assert session.phase == "tests"
    assert session.messages[-1].type == "lab_tutor"
    assert XLA.wrong_paths["cvid"] in session.messages[-1].text


async def test_submit_differentials_llm_path():
    service, llm = make_service(reply="differential feedback")
    session = await service.start_case("xla", "practice")
    await service.set_differentials(session.id, "Possibly a phagocyte disorder")

    session = await service.submit_differentials(session.id)

    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == make_differential_eval_prompt(XLA, "practice")
    assert call["messages"] == [
        {"role": "user", "content": "Possibly a phagocyte disorder"}
    ]
    assert call["max_tokens"] == 250
    assert session.phase == "tests"
    assert session.messages[-1].text == "💡 Clinical reasoning note:\ndifferential feedback"


async def test_submit_interpretation_calls_llm_and_sets_result():
    service, llm = make_service(reply="interp feedback")
    session = await service.start_case("xla", "practice")
    await set_phase(service, session.id, "interpretation")
    await service.set_interp_text(session.id, "B cells are absent")

    session = await service.submit_interpretation(session.id)

    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == make_interpretation_eval_prompt(XLA, "practice")
    assert call["messages"] == [{"role": "user", "content": "B cells are absent"}]
    assert call["max_tokens"] == 300
    assert session.interp_result == "interp feedback"
    assert session.phase == "interpretation"
    assert session.messages[-1].type == "lab_tutor"


async def test_submit_interpretation_error_path():
    service, _ = make_service(raises=True)
    session = await service.start_case("xla", "practice")
    await set_phase(service, session.id, "interpretation")
    await service.set_interp_text(session.id, "B cells are absent")

    session = await service.submit_interpretation(session.id)

    assert session.messages[-1].type == "lab_note"
    assert session.interp_result == "⚠ Connection error. Please try again."


async def test_submit_final_answer_parses_json_and_transitions():
    service, llm = make_service(structured=FEEDBACK_FIXTURE)
    session = await service.start_case("xla", "practice")
    await service.set_final_answer_field(session.id, "diagnosis", "XLA")
    await service.set_final_answer_field(session.id, "management", "IVIG")

    session = await service.submit_final_answer(session.id)

    assert len(llm.structured_calls) == 1
    call = llm.structured_calls[0]
    assert call["system"].startswith(make_feedback_prompt(XLA))
    assert "Student's final answer:" in call["system"]
    assert "Diagnosis: XLA" in call["system"]
    assert call["schema"] is FEEDBACK_SCHEMA
    assert call["max_tokens"] == 1500
    assert session.feedback == FEEDBACK_FIXTURE
    assert session.phase == "feedback"


async def test_submit_final_answer_error_appends_system_message():
    service, _ = make_service(raises=True)
    session = await service.start_case("xla", "practice")
    await service.set_final_answer_field(session.id, "diagnosis", "XLA")

    session = await service.submit_final_answer(session.id)

    assert session.feedback is None
    assert session.phase == "history"
    assert session.messages[-1].type == "system"
    assert session.messages[-1].text == "⚠ Could not generate structured feedback. Please try again."


async def test_request_hint_increments_before_context_and_calls_llm():
    service, llm = make_service(reply="here is a hint")
    session = await service.start_case("xla", "practice")

    hint = await service.request_hint(session.id)
    session = await service.get(session.id)

    assert hint == "here is a hint"
    assert session.hints_used == 1
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["messages"] == [{"role": "user", "content": "I need a hint."}]
    assert call["max_tokens"] == 200
    assert "HINTS USED SO FAR: 1" in call["system"]


async def test_request_hint_fallback_on_error():
    service, _ = make_service(raises=True)
    session = await service.start_case("xla", "practice")

    hint = await service.request_hint(session.id)
    session = await service.get(session.id)

    assert hint == HINT_FALLBACK
    assert session.hints_used == 1


async def test_request_hint_context_uses_current_messages():
    service, llm = make_service(reply="here is a hint")
    session = await service.start_case("xla", "practice")

    await service.request_hint(session.id)
    session = await service.get(session.id)

    msgs = [{"text": m.text, "type": m.type} for m in session.messages]
    expected_context = build_hint_context(XLA, "history", msgs, [], 1)
    assert llm.calls[0]["system"] == build_hint_system_prompt(
        expected_context["context"]
    )


async def test_submit_reflection_advances_steps_then_summarises():
    service, llm = make_service(reply="reflection summary")
    session = await service.start_case("xla", "reflection")
    await set_phase(service, session.id, "reflection")

    for i in range(4):
        session = await service.submit_reflection(session.id, f"answer {i}")
        assert session.reflection_step == i + 1
        assert llm.calls == []

    session = await service.submit_reflection(session.id, "final answer")

    assert len(session.reflection_answers) == 5
    assert session.reflection_answers[0]["q"] == REFLECTION_QS[0]
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == build_reflection_summary_prompt(XLA)
    assert call["max_tokens"] == 300
    assert "Q: " in call["messages"][0]["content"]
    assert session.messages[-1].type == "tutor"
    assert session.messages[-1].text == "reflection summary"


async def test_button_transition_go_to_summary():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.go_to_summary(session.id, "Please write a clinical summary.")

    assert session.phase == "summary"
    assert session.messages[-1].type == "tutor"
    assert session.messages[-1].text == "Please write a clinical summary."


async def test_button_transition_go_to_reflection():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    await set_phase(service, session.id, "feedback")

    session = await service.go_to_reflection(session.id)

    assert session.phase == "reflection"
    assert session.mode == "reflection"


async def test_button_transition_go_to_differential():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.go_to_differential(session.id, "Propose your differentials.")

    assert session.phase == "differential"
    assert session.messages[-1].type == "tutor"


async def test_button_transition_go_to_interpretation():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    await set_phase(service, session.id, "tests")

    session = await service.go_to_interpretation(session.id, "Interpret the results.")

    assert session.phase == "interpretation"
    assert session.messages[-1].type == "lab_tutor"


async def test_button_transition_go_to_final():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")

    session = await service.go_to_final(session.id, "Submit your final diagnosis.")

    assert session.phase == "final"
    assert session.messages[-1].type == "tutor"


async def test_button_transition_go_to_tests_clears_interp():
    service, _ = make_service()
    session = await service.start_case("xla", "practice")
    await set_phase(service, session.id, "interpretation")
    await service.set_interp_text(session.id, "something")
    await append_raw(
        service,
        session.id,
        EventType.INTERPRETATION_EVALUATED,
        {
            "interp_note_message_id": service._next_id(),
            "interp_note_text": "note",
            "result_message_id": service._next_id(),
            "result": "result",
            "error": False,
        },
    )

    session = await service.go_to_tests(session.id)

    assert session.phase == "tests"
    assert session.interp_text == ""
    assert session.interp_result == ""
