from __future__ import annotations

import itertools

import pytest

import app.content.cases as cases_module
from app.content.cases import XLA
from app.schemas.case import Case
from app.services import SessionService
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


class FakeLLMClient:
    def __init__(self, reply="canned-reply", raises=False):
        self._reply = reply
        self._raises = raises
        self.calls = []

    async def generate(self, system, messages, max_tokens):
        self.calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        if self._raises:
            raise RuntimeError("boom")
        return self._reply


def sequential_ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


def make_service(reply="canned-reply", rng=None, raises=False):
    llm = FakeLLMClient(reply=reply, raises=raises)
    service = SessionService(
        llm,
        rng=rng or (lambda: 0.0),
        id_factory=sequential_ids(),
    )
    return service, llm


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


def test_start_case_resets_and_appends_opening():
    service, llm = make_service()
    session = service.start_case("xla", "practice")

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


def test_start_case_unknown_case_raises():
    service, _ = make_service()
    with pytest.raises(KeyError):
        service.start_case("nope", "practice")


def test_send_message_test_order_branch():
    service, llm = make_service()
    session = service.start_case("xla", "practice")

    result = service.send_message(session, "Please order immunoglobulins and a CBC")

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


def test_send_message_test_order_genetic_nudge_in_practice():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.send_message(session, "order the immunodeficiency gene panel")

    assert "immunodeficiency gene panel" in session.ordered_tests
    lab_tutor = [m for m in session.messages if m.type == "lab_tutor"]
    assert len(lab_tutor) == 1
    assert lab_tutor[0].text.startswith("💡 Clinical reasoning note: Genetic testing")


def test_send_message_test_order_already_ordered():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    service.send_message(session, "order a CBC")
    before = len(session.messages)

    service.send_message(session, "order a CBC")

    assert session.messages[-1].text == "These investigations have already been ordered."
    assert len(session.messages) == before + 2


def _pad_history(service, session, count):
    for i in range(count):
        msg = service._add_msg(session, f"filler {i}", "student")  # noqa: SLF001
        assert msg.type == "student"


def test_send_message_scid_trigger_fires_when_rng_above_threshold(register_scid):
    service, llm = make_service(rng=lambda: 0.7)
    session = service.start_case("scid", "practice")
    _pad_history(service, session, 9)

    result = service.send_message(session, "tell me about the rash")

    assert result.branch == "scid"
    assert result.messages is None
    parent = [m for m in session.messages if m.type == "parent"]
    tutor = [m for m in session.messages if m.type == "tutor"]
    assert len(parent) == 1
    assert parent[0].text.startswith("Doctor, I am getting worried")
    assert len(tutor) == 1
    assert tutor[0].text.startswith("🟡 Clinical reasoning note")
    assert llm.calls == []


def test_send_message_scid_trigger_not_fired_when_rng_at_threshold(register_scid):
    service, _ = make_service(rng=lambda: 0.6)
    session = service.start_case("scid", "practice")
    _pad_history(service, session, 9)

    result = service.send_message(session, "tell me about the rash")

    assert result.branch == "parent"
    assert result.system == SCID.parent_prompt
    assert result.max_tokens == 300
    assert not any(m.text.startswith("Doctor, I am getting worried") for m in session.messages)


def test_send_message_scid_trigger_suppressed_by_urgent_keyword(register_scid):
    service, _ = make_service(rng=lambda: 0.99)
    session = service.start_case("scid", "practice")
    service._add_msg(session, "we should arrange urgent isolation", "student")  # noqa: SLF001
    _pad_history(service, session, 9)

    result = service.send_message(session, "tell me about the rash")

    assert result.branch == "parent"


def test_send_message_parent_branch_history_mapping():
    service, llm = make_service()
    session = service.start_case("xla", "practice")
    opening_text = session.messages[0].text
    service._add_msg(session, "When did it start?", "student")  # noqa: SLF001
    service._add_msg(session, "It started at six months.", "parent")  # noqa: SLF001
    service._add_msg(session, "__LAB__CBC\nWBC normal", "lab")  # noqa: SLF001

    result = service.send_message(session, "Any family history?")

    assert result.branch == "parent"
    assert result.system == XLA.parent_prompt
    assert result.max_tokens == 300
    assert result.messages == [
        {"role": "assistant", "content": opening_text},
        {"role": "user", "content": "When did it start?"},
        {"role": "assistant", "content": "It started at six months."},
        {"role": "assistant", "content": "[Lab result shown]"},
        {"role": "user", "content": "Any family history?"},
    ]
    assert llm.calls == []


def test_append_parent_reply_emits_nudge_on_fifth_parent_message():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    for _ in range(4):
        service.append_parent_reply(session, "reply")
    assert not any(m.text.startswith("💡 Clinical reasoning note: You have gathered") for m in session.messages)

    service.append_parent_reply(session, "fifth reply")

    nudges = [m for m in session.messages if m.text.startswith("💡 Clinical reasoning note: You have gathered")]
    assert len(nudges) == 1
    assert nudges[0].type == "tutor"


def test_append_parent_reply_no_nudge_in_exam_mode():
    service, _ = make_service()
    session = service.start_case("xla", "exam")
    for _ in range(5):
        service.append_parent_reply(session, "reply")
    assert not any(m.text.startswith("💡 Clinical reasoning note: You have gathered") for m in session.messages)


def test_request_exam_appends_findings_and_practice_note():
    service, llm = make_service()
    session = service.start_case("xla", "practice")

    service.request_exam(session)

    types = [m.type for m in session.messages[-3:]]
    assert types == ["student", "system", "tutor"]
    assert session.messages[-2].text.startswith("📋 Physical examination findings:")
    assert XLA.exam_findings in session.messages[-2].text
    assert session.exam_done is True
    assert session.phase == "history"
    assert llm.calls == []


def test_request_exam_no_note_in_exam_mode():
    service, _ = make_service()
    session = service.start_case("xla", "exam")

    service.request_exam(session)

    assert session.messages[-1].type == "system"
    assert session.exam_done is True


def test_send_test_order_not_recognised():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.send_test_order(session, "xyzzy nonsense")

    assert session.messages[-1].type == "lab_note"
    assert "was not recognised" in session.messages[-1].text
    assert session.ordered_tests == set()


def test_send_test_order_phase_jump_and_lab():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.send_test_order(session, "immunoglobulins")

    assert session.phase == "tests"
    assert "immunoglobulin" in session.ordered_tests
    assert session.messages[-1].type == "lab"
    assert session.messages[-1].text.startswith("__LAB__immunoglobulins")


def test_send_test_order_already_ordered_note():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    service.send_test_order(session, "CBC")

    service.send_test_order(session, "CBC")

    assert session.messages[-1].type == "lab_note"
    assert session.messages[-1].text == "These investigations have already been ordered."


async def test_submit_summary_calls_llm_and_transitions():
    service, llm = make_service(reply="good summary feedback")
    session = service.start_case("xla", "practice")
    service.set_summary(session, "My summary text")

    await service.submit_summary(session)

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
    session = service.start_case("xla", "practice")
    service.set_differentials(session, "I think this is CVID actually")

    await service.submit_differentials(session)

    assert llm.calls == []
    assert session.phase == "tests"
    assert session.messages[-1].type == "lab_tutor"
    assert XLA.wrong_paths["cvid"] in session.messages[-1].text


async def test_submit_differentials_llm_path():
    service, llm = make_service(reply="differential feedback")
    session = service.start_case("xla", "practice")
    service.set_differentials(session, "Possibly a phagocyte disorder")

    await service.submit_differentials(session)

    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == make_differential_eval_prompt(XLA, "practice")
    assert call["messages"] == [{"role": "user", "content": "Possibly a phagocyte disorder"}]
    assert call["max_tokens"] == 250
    assert session.phase == "tests"
    assert session.messages[-1].text == "💡 Clinical reasoning note:\ndifferential feedback"


async def test_submit_interpretation_calls_llm_and_sets_result():
    service, llm = make_service(reply="interp feedback")
    session = service.start_case("xla", "practice")
    session.phase = "interpretation"
    service.set_interp_text(session, "B cells are absent")

    await service.submit_interpretation(session)

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
    session = service.start_case("xla", "practice")
    session.phase = "interpretation"
    service.set_interp_text(session, "B cells are absent")

    await service.submit_interpretation(session)

    assert session.messages[-1].type == "lab_note"
    assert session.interp_result == "⚠ Connection error. Please try again."


async def test_submit_final_answer_parses_json_and_transitions():
    payload = '{"diagnosticAccuracy": "correct", "wellDone": ["x"]}'
    service, llm = make_service(reply="Here is feedback: " + payload + " thanks")
    session = service.start_case("xla", "practice")
    service.set_final_answer_field(session, "diagnosis", "XLA")
    service.set_final_answer_field(session, "management", "IVIG")

    await service.submit_final_answer(session)

    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"].startswith(make_feedback_prompt(XLA))
    assert "Student's final answer:" in call["system"]
    assert "Diagnosis: XLA" in call["system"]
    assert call["max_tokens"] == 1500
    assert session.feedback == {"diagnosticAccuracy": "correct", "wellDone": ["x"]}
    assert session.phase == "feedback"


async def test_submit_final_answer_error_appends_system_message():
    service, _ = make_service(raises=True)
    session = service.start_case("xla", "practice")
    service.set_final_answer_field(session, "diagnosis", "XLA")

    await service.submit_final_answer(session)

    assert session.feedback is None
    assert session.phase == "history"
    assert session.messages[-1].type == "system"
    assert session.messages[-1].text == "⚠ Could not generate structured feedback. Please try again."


async def test_request_hint_increments_before_context_and_calls_llm():
    service, llm = make_service(reply="here is a hint")
    session = service.start_case("xla", "practice")

    hint = await service.request_hint(session)

    assert hint == "here is a hint"
    assert session.hints_used == 1
    assert len(llm.calls) == 1
    call = llm.calls[0]
    expected_msgs = [{"text": m.text, "type": m.type} for m in session.messages]
    expected_context = build_hint_context(XLA, "history", expected_msgs, [], 1)
    assert call["system"] == build_hint_system_prompt(expected_context["context"])
    assert "HINTS USED SO FAR: 1" in call["system"]
    assert call["messages"] == [{"role": "user", "content": "I need a hint."}]
    assert call["max_tokens"] == 200


async def test_request_hint_fallback_on_error():
    service, _ = make_service(raises=True)
    session = service.start_case("xla", "practice")

    hint = await service.request_hint(session)

    assert hint == HINT_FALLBACK
    assert session.hints_used == 1


async def test_submit_reflection_advances_steps_then_summarises():
    service, llm = make_service(reply="reflection summary")
    session = service.start_case("xla", "reflection")
    session.phase = "reflection"

    for i in range(4):
        await service.submit_reflection(session, f"answer {i}")
        assert session.reflection_step == i + 1
        assert llm.calls == []

    await service.submit_reflection(session, "final answer")

    assert len(session.reflection_answers) == 5
    assert session.reflection_answers[0]["q"] == REFLECTION_QS[0]
    assert len(llm.calls) == 1
    call = llm.calls[0]
    assert call["system"] == build_reflection_summary_prompt(XLA)
    assert call["max_tokens"] == 300
    assert "Q: " in call["messages"][0]["content"]
    assert session.messages[-1].type == "tutor"
    assert session.messages[-1].text == "reflection summary"


def test_button_transition_go_to_summary():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.go_to_summary(session, "Please write a clinical summary.")

    assert session.phase == "summary"
    assert session.messages[-1].type == "tutor"
    assert session.messages[-1].text == "Please write a clinical summary."


def test_button_transition_go_to_reflection():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    session.phase = "feedback"

    service.go_to_reflection(session)

    assert session.phase == "reflection"
    assert session.mode == "reflection"


def test_button_transition_go_to_differential():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.go_to_differential(session, "Propose your differentials.")

    assert session.phase == "differential"
    assert session.messages[-1].type == "tutor"


def test_button_transition_go_to_interpretation():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    session.phase = "tests"

    service.go_to_interpretation(session, "Interpret the results.")

    assert session.phase == "interpretation"
    assert session.messages[-1].type == "lab_tutor"


def test_button_transition_go_to_final():
    service, _ = make_service()
    session = service.start_case("xla", "practice")

    service.go_to_final(session, "Submit your final diagnosis.")

    assert session.phase == "final"
    assert session.messages[-1].type == "tutor"


def test_button_transition_go_to_tests_clears_interp():
    service, _ = make_service()
    session = service.start_case("xla", "practice")
    session.phase = "interpretation"
    service.set_interp_text(session, "something")
    session.interp_result = "result"

    service.go_to_tests(session)

    assert session.phase == "tests"
    assert session.interp_text == ""
    assert session.interp_result == ""
