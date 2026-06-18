from __future__ import annotations

import itertools

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.runtime as runtime
from app.main import app
from app.services import SessionService


class FakeLLMClient:
    def __init__(self, reply="canned-reply"):
        self.reply = reply
        self.stream_chunks = ["Hello", " from", " the", " parent"]
        self.generate_calls = []
        self.stream_calls = []

    async def generate(self, system, messages, max_tokens):
        self.generate_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        return self.reply

    async def stream(self, system, messages, max_tokens):
        self.stream_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        for chunk in self.stream_chunks:
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
async def gql_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _gql(client, query, variables=None):
    resp = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert "errors" not in payload, payload
    return payload["data"]


START = """
mutation Start($caseId: String!, $mode: String!) {
  startCase(caseId: $caseId, mode: $mode) {
    id phase mode caseId messages { id type text }
  }
}
"""


async def test_query_case(fake_llm, gql_client):
    data = await _gql(
        gql_client,
        "query Q($id: String!) { case(id: $id) { id title targetDiagnosis } }",
        {"id": "xla"},
    )
    assert data["case"]["id"] == "xla"
    assert "Agammaglobulinaemia" in data["case"]["targetDiagnosis"]


async def test_query_case_unknown_returns_null(fake_llm, gql_client):
    data = await _gql(
        gql_client,
        "query Q($id: String!) { case(id: $id) { id } }",
        {"id": "nope"},
    )
    assert data["case"] is None


async def test_start_case_and_session_query(fake_llm, gql_client):
    data = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    session = data["startCase"]
    assert session["phase"] == "history"
    assert session["mode"] == "practice"
    assert len(session["messages"]) == 1
    assert session["messages"][0]["type"] == "system"

    fetched = await _gql(
        gql_client,
        "query Q($id: String!) { session(id: $id) { id phase orderedTests } }",
        {"id": session["id"]},
    )
    assert fetched["session"]["id"] == session["id"]
    assert fetched["session"]["orderedTests"] == []


async def test_send_message_test_order_branch(fake_llm, gql_client):
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    data = await _gql(
        gql_client,
        """
        mutation Send($id: String!, $text: String!) {
          sendMessage(sessionId: $id, text: $text) {
            branch
            session { phase orderedTests messages { type } }
          }
        }
        """,
        {"id": sid, "text": "order immunoglobulins and a CBC"},
    )
    result = data["sendMessage"]
    assert result["branch"] == "TESTS"
    assert result["session"]["phase"] == "tests"
    assert set(result["session"]["orderedTests"]) == {"immunoglobulin", "CBC"}
    assert fake_llm.generate_calls == []


async def test_send_message_parent_branch_stores_pending(fake_llm, gql_client):
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    data = await _gql(
        gql_client,
        """
        mutation Send($id: String!, $text: String!) {
          sendMessage(sessionId: $id, text: $text) { branch session { id } }
        }
        """,
        {"id": sid, "text": "When did the infections start?"},
    )
    assert data["sendMessage"]["branch"] == "PARENT"
    session = runtime.get_session_service().get(sid)
    assert session.pending_parent is not None
    assert session.pending_parent.branch == "parent"


async def test_request_exam_and_summary_flow(fake_llm, gql_client):
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    exam = await _gql(
        gql_client,
        "mutation E($id: String!) { requestExam(sessionId: $id) { examDone } }",
        {"id": sid},
    )
    assert exam["requestExam"]["examDone"] is True

    await _gql(
        gql_client,
        'mutation S($id: String!) { setSummary(sessionId: $id, value: "my summary") { summary } }',
        {"id": sid},
    )
    submitted = await _gql(
        gql_client,
        "mutation U($id: String!) { submitSummary(sessionId: $id) { phase messages { type text } } }",
        {"id": sid},
    )
    assert submitted["submitSummary"]["phase"] == "examination"
    assert len(fake_llm.generate_calls) == 1
    assert fake_llm.generate_calls[0]["max_tokens"] == 300


async def test_submit_final_answer_input_and_feedback(fake_llm, gql_client):
    fake_llm.reply = (
        '{"diagnosticAccuracy": "correct", "diagnosticComment": "good", '
        '"wellDone": ["a"], "missing": ["b"], "keyClues": ["c"], '
        '"reasoningPathway": "path", "managementPoints": ["m"], '
        '"geneticPoints": ["g"], "revisionTopic": "topic", '
        '"scores": {"historyTaking": "Good", "examination": "Good", '
        '"differential": "Good", "testSelection": "Good", '
        '"interpretation": "Good", "management": "Good"}}'
    )
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    data = await _gql(
        gql_client,
        """
        mutation F($id: String!, $a: FinalAnswerInput!) {
          submitFinalAnswer(sessionId: $id, answer: $a) {
            phase
            feedback {
              diagnosticAccuracy wellDone missing keyClues
              reasoningPathway managementPoints geneticPoints revisionTopic
              scores { historyTaking management }
            }
          }
        }
        """,
        {
            "id": sid,
            "a": {
                "diagnosis": "XLA",
                "findings": "no B cells",
                "differentials": "",
                "tests": "",
                "management": "IVIG",
                "genetics": "",
                "explanation": "",
            },
        },
    )
    result = data["submitFinalAnswer"]
    assert result["phase"] == "feedback"
    assert result["feedback"]["diagnosticAccuracy"] == "correct"
    assert result["feedback"]["wellDone"] == ["a"]
    assert result["feedback"]["scores"]["management"] == "Good"
    assert fake_llm.generate_calls[0]["max_tokens"] == 1500


async def test_request_hint_returns_string(fake_llm, gql_client):
    fake_llm.reply = "here is your hint"
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    data = await _gql(
        gql_client,
        "mutation H($id: String!) { requestHint(sessionId: $id) }",
        {"id": sid},
    )
    assert data["requestHint"] == "here is your hint"


async def test_pure_transition_propose_differentials(fake_llm, gql_client):
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]

    data = await _gql(
        gql_client,
        """
        mutation P($id: String!, $p: String!) {
          proposeDifferentials(sessionId: $id, prompt: $p) {
            phase messages { type text }
          }
        }
        """,
        {"id": sid, "p": "Propose your differentials."},
    )
    result = data["proposeDifferentials"]
    assert result["phase"] == "differential"
    assert result["messages"][-1]["type"] == "tutor"
    assert result["messages"][-1]["text"] == "Propose your differentials."


async def test_send_message_unknown_session_errors(fake_llm, gql_client):
    resp = await gql_client.post(
        "/graphql",
        json={
            "query": "mutation { sendMessage(sessionId: \"nope\", text: \"hi\") { branch } }"
        },
    )
    payload = resp.json()
    assert payload.get("errors")
