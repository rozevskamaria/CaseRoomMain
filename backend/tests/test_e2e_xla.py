from __future__ import annotations

import itertools
import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.runtime as runtime
from app.content.cases import get_case
from app.main import app
from app.services import SessionService

FEEDBACK_JSON = {
    "diagnosticAccuracy": "correct",
    "diagnosticComment": "XLA is the correct diagnosis.",
    "wellDone": ["Recognised the absent B cells", "Spotted the X-linked family history"],
    "missing": ["Could have screened for Giardia earlier"],
    "keyClues": ["Onset at 6 months", "Absent tonsils", "Absent CD19 B cells"],
    "reasoningPathway": "Recurrent encapsulated infections from 6m, absent B cells, BTK variant.",
    "managementPoints": ["Start IVIG", "Contraindicate live vaccines"],
    "geneticPoints": ["X-linked recessive", "Mother obligate carrier"],
    "revisionTopic": "Approach to recurrent bacterial infection in infancy.",
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
    def __init__(self) -> None:
        self.parent_chunks = [
            "He started getting infections ",
            "at about six months of age. ",
            "Before that he was healthy.",
        ]
        self.generate_calls: list[dict] = []
        self.structured_calls: list[dict] = []
        self.stream_calls: list[dict] = []

    async def generate_structured(self, system, messages, schema, max_tokens):
        self.structured_calls.append(
            {
                "system": system,
                "messages": messages,
                "schema": schema,
                "max_tokens": max_tokens,
            }
        )
        return FEEDBACK_JSON

    async def generate(self, system, messages, max_tokens):
        self.generate_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        if "CONTEXTUAL HINT" in system:
            return "Consider which immune compartment the infection pattern points to."
        if "summarising a medical student's reflection" in system:
            return "You reasoned through the antibody-deficiency pattern well."
        return "Good reasoning — consider the B-cell compartment next."

    async def stream(self, system, messages, max_tokens):
        self.stream_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        for chunk in self.parent_chunks:
            yield chunk


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


@pytest.fixture
def fake_llm():
    llm = FakeLLMClient()
    service = SessionService(llm, rng=lambda: 0.0, id_factory=_ids())
    runtime.set_llm_client(llm)
    runtime.set_session_service(service)
    yield llm
    runtime.reset()


@pytest_asyncio.fixture
async def client(student_principal):
    from tests.conftest import auth_cookies

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies=auth_cookies(student_principal),
    ) as ac:
        yield ac


async def _gql(client, query, variables=None):
    resp = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert "errors" not in payload, payload
    return payload["data"]


def _parent_deltas(body: str) -> list[str]:
    out = []
    for line in body.splitlines():
        if line.startswith("data: "):
            payload = json.loads(line[len("data: "):])
            if "delta" in payload:
                out.append(payload["delta"])
    return out


START = """
mutation Start($caseId: String!, $mode: String!) {
  startCase(caseId: $caseId, mode: $mode) {
    id phase mode caseId messages { id type text }
  }
}
"""

SEND = """
mutation Send($id: String!, $text: String!) {
  sendMessage(sessionId: $id, text: $text) {
    branch
    session { id phase orderedTests messages { type text } }
  }
}
"""

SESSION = """
query S($id: String!) {
  session(id: $id) {
    id phase orderedTests hintsUsed examDone reflectionStep
    messages { type text }
  }
}
"""


async def _drive_parent_sse(client, sid: str) -> list[str]:
    resp = await client.get(f"/sse/parent/{sid}")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"done": true}' in resp.text
    return _parent_deltas(resp.text)


async def test_full_xla_playthrough(fake_llm, client):
    case = get_case("xla")

    started = await _gql(client, START, {"caseId": "xla", "mode": "practice"})
    session = started["startCase"]
    sid = session["id"]
    assert session["phase"] == "history"
    assert session["mode"] == "practice"
    assert len(session["messages"]) == 1
    opening = session["messages"][0]
    assert opening["type"] == "system"
    assert opening["text"].startswith("📍 Immunology Department — Outpatient Clinic")
    assert case.opening_clinical in opening["text"]

    history_questions = [
        "When did the infections start?",
        "What kind of infections has he had?",
        "Has he had all his vaccines?",
        "Are there any unexplained deaths in the family?",
        "How is his growth and weight?",
    ]
    full_parent_reply = "".join(fake_llm.parent_chunks)
    for i, q in enumerate(history_questions, start=1):
        send = await _gql(client, SEND, {"id": sid, "text": q})
        assert send["sendMessage"]["branch"] == "PARENT", q
        assert send["sendMessage"]["session"]["phase"] == "history"

        deltas = await _drive_parent_sse(client, sid)
        assert deltas == fake_llm.parent_chunks

        assert fake_llm.stream_calls[-1]["max_tokens"] == 300
        assert fake_llm.stream_calls[-1]["system"] == case.parent_prompt

        sess = (await _gql(client, SESSION, {"id": sid}))["session"]
        parent_msgs = [m for m in sess["messages"] if m["type"] == "parent"]
        assert len(parent_msgs) == i
        assert parent_msgs[-1]["text"] == full_parent_reply

    sess = (await _gql(client, SESSION, {"id": sid}))["session"]
    nudges = [
        m
        for m in sess["messages"]
        if m["type"] == "tutor"
        and m["text"].startswith("💡 Clinical reasoning note: You have gathered")
    ]
    assert len(nudges) == 1, "parent-count==5 proactive exam nudge should fire once"
    assert fake_llm.generate_calls == []

    send = await _gql(
        client, SEND, {"id": sid, "text": "I'd like to order immunoglobulins and a CBC"}
    )
    result = send["sendMessage"]
    assert result["branch"] == "TESTS"
    assert result["session"]["phase"] == "tests"
    assert set(result["session"]["orderedTests"]) == {"immunoglobulin", "CBC"}
    lab_msgs = [m for m in result["session"]["messages"] if m["type"] == "lab"]
    ig_lab = next((m for m in lab_msgs if m["text"].startswith("__LAB__immunoglobulins")), None)
    assert ig_lab is not None, "immunoglobulins lab not appended"
    assert "IgG: <100" in ig_lab["text"]
    assert "IgA: <5" in ig_lab["text"]
    assert "CD19" not in ig_lab["text"]
    cbc_lab = next(
        (m for m in lab_msgs if m["text"].startswith("__LAB__CBC / full blood count")), None
    )
    assert cbc_lab is not None, "CBC lab not appended"
    assert fake_llm.generate_calls == []

    exam = await _gql(
        client,
        "mutation E($id: String!) { requestExam(sessionId: $id) { examDone phase messages { type text } } }",
        {"id": sid},
    )
    ex = exam["requestExam"]
    assert ex["examDone"] is True
    assert ex["phase"] == "tests"
    exam_finding_msg = next(
        (m for m in ex["messages"] if m["text"].startswith("📋 Physical examination findings:")),
        None,
    )
    assert exam_finding_msg is not None
    assert case.exam_findings in exam_finding_msg["text"]
    assert ex["messages"][-1]["type"] == "tutor"

    await _gql(
        client,
        "mutation P($id: String!, $p: String!) { proposeDifferentials(sessionId: $id, prompt: $p) { phase messages { type text } } }",
        {"id": sid, "p": "Propose your differentials."},
    )
    await _gql(
        client,
        'mutation D($id: String!, $v: String!) { setDifferentials(sessionId: $id, value: $v) { differentials } }',
        {"id": sid, "v": "I think this is CVID"},
    )
    gen_before = len(fake_llm.generate_calls)
    wrong = await _gql(
        client,
        "mutation SD($id: String!) { submitDifferentials(sessionId: $id) { phase messages { type text } } }",
        {"id": sid},
    )
    assert len(fake_llm.generate_calls) == gen_before, "wrong path must not call LLM"
    assert wrong["submitDifferentials"]["phase"] == "tests"
    wp_msg = wrong["submitDifferentials"]["messages"][-1]
    assert wp_msg["type"] == "lab_tutor"
    assert case.wrong_paths["cvid"] in wp_msg["text"]

    await _gql(
        client,
        "mutation P($id: String!, $p: String!) { proposeDifferentials(sessionId: $id, prompt: $p) { phase } }",
        {"id": sid, "p": "Reconsider your differentials."},
    )
    await _gql(
        client,
        'mutation D($id: String!, $v: String!) { setDifferentials(sessionId: $id, value: $v) { differentials } }',
        {"id": sid, "v": "X-linked agammaglobulinaemia given absent B cells"},
    )
    gen_before = len(fake_llm.generate_calls)
    correct = await _gql(
        client,
        "mutation SD($id: String!) { submitDifferentials(sessionId: $id) { phase messages { type text } } }",
        {"id": sid},
    )
    assert len(fake_llm.generate_calls) == gen_before + 1, "correct path must call LLM once"
    assert fake_llm.generate_calls[-1]["max_tokens"] == 250
    assert correct["submitDifferentials"]["phase"] == "tests"
    assert correct["submitDifferentials"]["messages"][-1]["type"] == "lab_tutor"

    await _gql(
        client,
        "mutation I($id: String!, $p: String!) { interpretResults(sessionId: $id, prompt: $p) { phase } }",
        {"id": sid, "p": "Interpret the results."},
    )
    await _gql(
        client,
        'mutation SI($id: String!, $v: String!) { setInterpretation(sessionId: $id, value: $v) { interpText } }',
        {"id": sid, "v": "Absent B cells with absent immunoglobulins fit XLA."},
    )
    gen_before = len(fake_llm.generate_calls)
    interp = await _gql(
        client,
        "mutation SUI($id: String!) { submitInterpretation(sessionId: $id) { phase interpResult messages { type text } } }",
        {"id": sid},
    )
    assert len(fake_llm.generate_calls) == gen_before + 1
    assert fake_llm.generate_calls[-1]["max_tokens"] == 300
    assert interp["submitInterpretation"]["phase"] == "interpretation"
    assert interp["submitInterpretation"]["interpResult"] != ""
    assert interp["submitInterpretation"]["messages"][-1]["type"] == "lab_tutor"

    sess_before = (await _gql(client, SESSION, {"id": sid}))["session"]
    assert sess_before["hintsUsed"] == 0
    gen_before = len(fake_llm.generate_calls)
    hint = await _gql(
        client,
        "mutation H($id: String!) { requestHint(sessionId: $id) }",
        {"id": sid},
    )
    assert isinstance(hint["requestHint"], str) and hint["requestHint"]
    assert len(fake_llm.generate_calls) == gen_before + 1
    assert fake_llm.generate_calls[-1]["max_tokens"] == 200
    sess_after = (await _gql(client, SESSION, {"id": sid}))["session"]
    assert sess_after["hintsUsed"] == 1

    structured_before = len(fake_llm.structured_calls)
    final = await _gql(
        client,
        """
        mutation F($id: String!, $a: FinalAnswerInput!) {
          submitFinalAnswer(sessionId: $id, answer: $a) {
            phase
            feedback {
              diagnosticAccuracy diagnosticComment wellDone missing keyClues
              reasoningPathway managementPoints geneticPoints revisionTopic
              scores { historyTaking examination differential testSelection interpretation management }
            }
          }
        }
        """,
        {
            "id": sid,
            "a": {
                "diagnosis": "X-linked agammaglobulinaemia (XLA)",
                "findings": "Absent B cells, absent tonsils, infections from 6 months",
                "differentials": "CVID, THI",
                "tests": "Immunoglobulins, flow cytometry, BTK panel",
                "management": "IVIG, treat Giardia, no live vaccines",
                "genetics": "X-linked recessive, mother is carrier",
                "explanation": "His immune system cannot make antibodies.",
            },
        },
    )
    fr = final["submitFinalAnswer"]
    assert fr["phase"] == "feedback"
    assert len(fake_llm.structured_calls) == structured_before + 1
    assert fake_llm.structured_calls[-1]["max_tokens"] == 1500
    fb = fr["feedback"]
    assert fb is not None, "feedback object should come from the structured output"
    assert fb["diagnosticAccuracy"] == "correct"
    assert fb["wellDone"] == FEEDBACK_JSON["wellDone"]
    assert fb["keyClues"] == FEEDBACK_JSON["keyClues"]
    assert fb["managementPoints"] == FEEDBACK_JSON["managementPoints"]
    assert fb["geneticPoints"] == FEEDBACK_JSON["geneticPoints"]
    assert fb["revisionTopic"] == FEEDBACK_JSON["revisionTopic"]
    assert fb["scores"]["differential"] == "Excellent"
    assert fb["scores"]["management"] == "Good"

    final_sys = fake_llm.structured_calls[-1]["system"]
    assert "Student's final answer:" in final_sys
    assert "X-linked agammaglobulinaemia (XLA)" in final_sys


async def test_reflection_steps(fake_llm, client):
    started = await _gql(client, START, {"caseId": "xla", "mode": "reflection"})
    sid = started["startCase"]["id"]

    REFLECT = "mutation R($id: String!, $t: String!) { submitReflection(sessionId: $id, text: $t) { reflectionStep messages { type text } } }"

    r1 = await _gql(client, REFLECT, {"id": sid, "t": "I suspected an antibody problem."})
    assert r1["submitReflection"]["reflectionStep"] == 1
    assert fake_llm.generate_calls == []

    r2 = await _gql(client, REFLECT, {"id": sid, "t": "The absent B cells changed my mind."})
    assert r2["submitReflection"]["reflectionStep"] == 2
    assert fake_llm.generate_calls == []

    await _gql(client, REFLECT, {"id": sid, "t": "I felt stuck before flow cytometry."})
    last = await _gql(client, REFLECT, {"id": sid, "t": "I would order immunoglobulins sooner."})
    assert last["submitReflection"]["reflectionStep"] == 4
    assert fake_llm.generate_calls == []

    final = await _gql(
        client, REFLECT, {"id": sid, "t": "The key lesson is age of onset narrows the differential."}
    )
    assert len(fake_llm.generate_calls) == 1
    assert fake_llm.generate_calls[0]["max_tokens"] == 300
    assert final["submitReflection"]["messages"][-1]["type"] == "tutor"


async def test_no_real_network_anthropic_never_instantiated(fake_llm, client):
    from app.llm.client import LLMClient

    real = runtime.get_llm_client()
    assert isinstance(real, FakeLLMClient)

    fresh = LLMClient()
    assert fresh._client is None  # noqa: SLF001
