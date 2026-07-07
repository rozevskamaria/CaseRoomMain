from __future__ import annotations

import itertools

import pytest

from app.llm.client import ToolCall, ToolRunResult
from app.services import SessionService
from app.services.prompts import (
    LANGUAGE_DIRECTIVE_LV,
    make_differential_eval_prompt,
    make_feedback_prompt,
    make_summary_eval_prompt,
)
from app.services.routing import build_case_tools, case_test_keys


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


class ToolFakeLLM:
    def __init__(self, tool_result: ToolRunResult, reply="canned"):
        self._tool_result = tool_result
        self._reply = reply
        self.structured = {}
        self.tool_calls = []
        self.generate_calls = []

    async def generate(self, system, messages, max_tokens):
        self.generate_calls.append({"system": system, "max_tokens": max_tokens})
        return self._reply

    async def generate_structured(self, system, messages, schema, max_tokens):
        self.generate_calls.append({"system": system, "schema": schema})
        return self.structured

    async def generate_with_tools(self, system, messages, tools, max_tokens=512):
        self.tool_calls.append(
            {"system": system, "messages": messages, "tools": tools}
        )
        return self._tool_result

    async def stream(self, system, messages, max_tokens):
        for chunk in ("a", "b"):
            yield chunk


def _order_test_result(keys):
    return ToolRunResult(
        tool_calls=[
            ToolCall(id="toolu_1", name="order_test", input={"test_names": keys})
        ]
    )


def _exam_result():
    return ToolRunResult(
        tool_calls=[ToolCall(id="toolu_1", name="request_exam", input={})]
    )


def _ask_parent_result(text):
    return ToolRunResult(
        tool_calls=[
            ToolCall(id="toolu_1", name="ask_parent", input={"utterance": text})
        ]
    )


def make_tool_service(tool_result, language="lv", reply="canned"):
    llm = ToolFakeLLM(tool_result, reply=reply)
    service = SessionService(llm, rng=lambda: 0.0, id_factory=_ids())
    return service, llm


def make_heuristic_service(reply="canned"):
    llm = ToolFakeLLM(ToolRunResult(), reply=reply)
    service = SessionService(llm, rng=lambda: 0.0, id_factory=_ids())
    return service, llm


def _events(session):
    return [(m.type, m.text) for m in session.messages]


async def test_case_tools_enum_uses_canonical_keys():
    from app.content.cases.xla import XLA

    tools = build_case_tools(XLA)
    order_tool = next(t for t in tools if t["name"] == "order_test")
    enum = order_tool["input_schema"]["properties"]["test_names"]["items"]["enum"]
    assert "CBC" in enum
    assert "immunoglobulin" in enum
    assert "immunodeficiency gene panel" in enum
    assert "CBC / full blood count" not in enum
    assert enum == case_test_keys(XLA)


async def test_tool_use_order_test_matches_heuristic_events():
    h_service, _ = make_heuristic_service()
    en = await h_service.start_case("xla", "practice")
    _, en = await h_service.send_message(
        en.id, "Please order immunoglobulins and a CBC"
    )

    t_service, llm = make_tool_service(_order_test_result(["CBC", "immunoglobulin"]))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "kaut kāds teksts")

    assert result.branch == "tests"
    assert lv.phase == "tests"
    assert lv.ordered_tests == {"CBC", "immunoglobulin"}
    assert len(llm.tool_calls) == 1

    en_after_student = [
        (m.type, m.text)
        for m in en.messages
        if not (m.type == "student")
    ]
    lv_after_student = [
        (m.type, m.text)
        for m in lv.messages
        if not (m.type == "student")
    ]
    assert lv_after_student == en_after_student


async def test_tool_use_genetic_nudge_parity():
    h_service, _ = make_heuristic_service()
    en = await h_service.start_case("xla", "practice")
    _, en = await h_service.send_message(en.id, "order the immunodeficiency gene panel")

    t_service, _ = make_tool_service(
        _order_test_result(["immunodeficiency gene panel"])
    )
    lv = await t_service.start_case("xla", "practice", language="lv")
    _, lv = await t_service.send_message(lv.id, "ģenētiskais tests lūdzu")

    en_lab_tutor = [m.text for m in en.messages if m.type == "lab_tutor"]
    lv_lab_tutor = [m.text for m in lv.messages if m.type == "lab_tutor"]
    assert lv_lab_tutor == en_lab_tutor
    assert len(lv_lab_tutor) == 1


async def test_tool_use_request_exam_produces_exam_performed():
    t_service, _ = make_tool_service(_exam_result())
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "apskatīt pacientu")

    assert result.branch == "tests"
    assert lv.exam_done is True
    assert any(
        m.text.startswith("📋 Physical examination findings:") for m in lv.messages
    )


async def test_tool_use_ask_parent_requests_parent_reply():
    t_service, _ = make_tool_service(_ask_parent_result("kad sākās?"))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "kad sākās simptomi?")

    assert result.branch == "parent"
    assert result.messages[-1] == {"role": "user", "content": "kad sākās simptomi?"}


async def test_tool_use_no_tool_falls_back_to_parent():
    t_service, _ = make_tool_service(ToolRunResult(tool_calls=[]))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "sveiki")

    assert result.branch == "parent"


async def test_tool_use_refusal_falls_back_to_parent():
    t_service, _ = make_tool_service(ToolRunResult(refused=True))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "sveiki")

    assert result.branch == "parent"


async def test_tool_use_llm_error_falls_back_to_parent():
    class RaisingLLM(ToolFakeLLM):
        async def generate_with_tools(self, system, messages, tools, max_tokens=512):
            raise RuntimeError("boom")

    llm = RaisingLLM(ToolRunResult())
    service = SessionService(llm, rng=lambda: 0.0, id_factory=_ids())
    lv = await service.start_case("xla", "practice", language="lv")
    result, lv = await service.send_message(lv.id, "sveiki")

    assert result.branch == "parent"


async def test_tool_use_non_enum_key_falls_back_to_parent():
    t_service, _ = make_tool_service(_order_test_result(["not-a-real-key"]))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, lv = await t_service.send_message(lv.id, "kaut kas")

    assert result.branch == "parent"


async def test_lv_parent_directive_in_parent_reply_system():
    t_service, _ = make_tool_service(_ask_parent_result("kad?"))
    lv = await t_service.start_case("xla", "practice", language="lv")
    result, _ = await t_service.send_message(lv.id, "kad sākās?")

    assert LANGUAGE_DIRECTIVE_LV in result.system
    from app.content.cases.xla import XLA

    assert result.system.startswith(XLA.parent_prompt)


async def test_lv_directive_present_in_tutor_and_feedback_prompts():
    from app.content.cases.xla import XLA

    assert LANGUAGE_DIRECTIVE_LV in make_summary_eval_prompt(XLA, "practice", "lv")
    assert LANGUAGE_DIRECTIVE_LV in make_differential_eval_prompt(
        XLA, "practice", "lv"
    )
    assert LANGUAGE_DIRECTIVE_LV in make_feedback_prompt(XLA, "lv")
    assert LANGUAGE_DIRECTIVE_LV not in make_summary_eval_prompt(XLA, "practice", "en")


async def test_lv_feedback_schema_keys_unchanged():
    from app.content.cases.xla import XLA
    from app.services.prompts import FEEDBACK_SCHEMA

    prompt = make_feedback_prompt(XLA, "lv")
    assert '"diagnosticAccuracy"' in prompt
    assert '"scores"' in prompt
    assert "correct|partially_correct|incorrect" in prompt
    assert set(FEEDBACK_SCHEMA["required"]) == {
        "diagnosticAccuracy",
        "diagnosticComment",
        "wellDone",
        "missing",
        "keyClues",
        "reasoningPathway",
        "managementPoints",
        "geneticPoints",
        "revisionTopic",
        "scores",
    }


async def test_start_case_localized_sets_language_on_projection():
    t_service, _ = make_tool_service(ToolRunResult())
    lv = await t_service.start_case("xla", "practice", language="lv")
    assert lv.language == "lv"

    fetched = await t_service.get(lv.id)
    assert fetched.language == "lv"


async def test_start_case_defaults_to_english():
    service, _ = make_heuristic_service()
    en = await service.start_case("xla", "practice")
    assert en.language == "en"


async def test_start_case_rejects_unknown_language():
    service, _ = make_heuristic_service()
    with pytest.raises(ValueError):
        await service.start_case("xla", "practice", language="ru")


async def test_send_test_order_shared_resolver_lab_and_phase():
    service, _ = make_heuristic_service()
    session = await service.start_case("xla", "practice")

    session = await service.send_test_order(session.id, "immunoglobulins")

    assert session.phase == "tests"
    assert "immunoglobulin" in session.ordered_tests
    assert session.messages[-1].type == "lab"
    assert session.messages[-1].text.startswith("__LAB__immunoglobulins")


async def test_send_test_order_already_ordered_uses_lab_note_channel():
    service, _ = make_heuristic_service()
    session = await service.start_case("xla", "practice")
    await service.send_test_order(session.id, "CBC")

    session = await service.send_test_order(session.id, "CBC")

    assert session.messages[-1].type == "lab_note"
    assert (
        session.messages[-1].text == "These investigations have already been ordered."
    )


async def test_send_test_order_no_batch_note_when_new():
    service, _ = make_heuristic_service()
    session = await service.start_case("xla", "practice")

    session = await service.send_test_order(session.id, "CBC")

    assert not any(
        m.text == "These investigations have already been ordered."
        for m in session.messages
    )
    assert not any(
        m.text.startswith("🔬 Investigations ordered") for m in session.messages
    )


async def test_send_message_always_emits_batch_note_when_new():
    service, _ = make_heuristic_service()
    session = await service.start_case("xla", "practice")

    _, session = await service.send_message(session.id, "order a CBC")

    assert session.messages[-1].type == "system"
    assert session.messages[-1].text.startswith("🔬 Investigations ordered")
