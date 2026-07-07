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
        self.structured = {}
        self.stream_chunks = ["Hello", " from", " the", " parent"]
        self.generate_calls = []
        self.structured_calls = []
        self.stream_calls = []

    async def generate(self, system, messages, max_tokens):
        self.generate_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        return self.reply

    async def generate_structured(self, system, messages, schema, max_tokens):
        self.structured_calls.append(
            {
                "system": system,
                "messages": messages,
                "schema": schema,
                "max_tokens": max_tokens,
            }
        )
        return self.structured

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
async def gql_client(student_principal):
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


START_LOCALIZED = """
mutation StartL($caseId: String!, $mode: String!, $language: String!) {
  startCaseLocalized(caseId: $caseId, mode: $mode, language: $language) {
    id phase mode language caseId
  }
}
"""


async def test_start_case_defaults_to_english_language(fake_llm, gql_client):
    data = await _gql(
        gql_client,
        "mutation S($c: String!, $m: String!) { startCase(caseId: $c, mode: $m) { id language } }",
        {"c": "xla", "m": "practice"},
    )
    assert data["startCase"]["language"] == "en"


async def test_start_case_localized_sets_language(fake_llm, gql_client):
    data = await _gql(
        gql_client,
        START_LOCALIZED,
        {"caseId": "xla", "mode": "practice", "language": "lv"},
    )
    session = data["startCaseLocalized"]
    assert session["language"] == "lv"
    assert session["phase"] == "history"

    fetched = await _gql(
        gql_client,
        "query Q($id: String!) { session(id: $id) { id language } }",
        {"id": session["id"]},
    )
    assert fetched["session"]["language"] == "lv"


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


async def test_send_message_parent_branch_records_request(fake_llm, gql_client):
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
    store = runtime.get_session_service()._store
    events = await store.load_events(sid)
    requests = [e for e in events if e.type == "ParentReplyRequested"]
    appended = [e for e in events if e.type == "ParentReplyAppended"]
    assert len(requests) == 1
    assert appended == []
    assert requests[0].data["max_tokens"] == 300


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
    fake_llm.structured = {
        "diagnosticAccuracy": "correct",
        "diagnosticComment": "good",
        "wellDone": ["a"],
        "missing": ["b"],
        "keyClues": ["c"],
        "reasoningPathway": "path",
        "managementPoints": ["m"],
        "geneticPoints": ["g"],
        "revisionTopic": "topic",
        "scores": {
            "historyTaking": "Good",
            "examination": "Good",
            "differential": "Good",
            "testSelection": "Good",
            "interpretation": "Good",
            "management": "Good",
        },
    }
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
    assert fake_llm.structured_calls[0]["max_tokens"] == 1500


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


async def test_attempt_query_returns_typed_event_timeline(fake_llm, gql_client):
    started = await _gql(gql_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]
    await _gql(
        gql_client,
        """
        mutation Send($id: String!, $text: String!) {
          sendMessage(sessionId: $id, text: $text) { branch }
        }
        """,
        {"id": sid, "text": "order a CBC"},
    )

    data = await _gql(
        gql_client,
        """
        query A($id: String!) {
          attempt(id: $id) {
            id caseId phase status
            events {
              __typename seq type
              ... on TestOrderedEvent { key }
              ... on PhaseChangedEvent { fromPhase toPhase }
            }
          }
        }
        """,
        {"id": sid},
    )
    attempt = data["attempt"]
    assert attempt["id"] == sid
    assert attempt["caseId"] == "xla"
    assert attempt["phase"] == "tests"
    typenames = [e["__typename"] for e in attempt["events"]]
    assert "SessionStartedEvent" in typenames
    assert "TestOrderedEvent" in typenames
    ordered = [
        e["key"] for e in attempt["events"] if e["__typename"] == "TestOrderedEvent"
    ]
    assert ordered == ["CBC"]


async def test_attempt_query_unknown_is_forbidden_for_non_owner(fake_llm, gql_client):
    resp = await gql_client.post(
        "/graphql",
        json={"query": 'query { attempt(id: "nope") { id } }'},
    )
    payload = resp.json()
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]
