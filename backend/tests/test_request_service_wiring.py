from __future__ import annotations

import itertools
import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.runtime as runtime
from app.main import app
from app.services import SessionService
from app.services.stores import InMemoryAttemptStore, RegistryCaseSource


class FakeLLMClient:
    def __init__(self):
        self.stream_chunks = ["He started ", "at six ", "months."]
        self.generate_calls = []
        self.stream_calls = []

    async def generate(self, system, messages, max_tokens):
        self.generate_calls.append(
            {"system": system, "messages": messages, "max_tokens": max_tokens}
        )
        return "canned"

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
def request_scoped_backend():
    llm = FakeLLMClient()
    shared_store = InMemoryAttemptStore()
    built_sessions: list[object] = []

    def factory(session):
        built_sessions.append(session)
        return SessionService(
            llm,
            store=shared_store,
            cases=RegistryCaseSource(),
            rng=lambda: 0.0,
            id_factory=_ids(),
        )

    runtime.set_llm_client(llm)
    runtime.set_service_factory(factory)
    yield llm, built_sessions
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
    session { id phase messages { type text } }
  }
}
"""

SESSION = """
query S($id: String!) {
  session(id: $id) { id phase messages { type text } }
}
"""

ATTEMPT_EVENTS = """
query AE($id: String!) {
  attempt(id: $id) { id events { __typename } }
}
"""


async def test_factory_routes_requests_through_per_request_service(
    request_scoped_backend, client
):
    _, built_sessions = request_scoped_backend

    started = await _gql(client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]
    assert started["startCase"]["phase"] == "history"
    assert len(started["startCase"]["messages"]) == 1

    fetched = (await _gql(client, SESSION, {"id": sid}))["session"]
    assert fetched["id"] == sid

    events = (await _gql(client, ATTEMPT_EVENTS, {"id": sid}))["attempt"]["events"]
    assert [e["__typename"] for e in events] == [
        "SessionStartedEvent",
        "SystemMessageEvent",
    ]

    assert len(built_sessions) >= 3


async def test_db_path_sse_parent_handoff(request_scoped_backend, client):
    llm, _ = request_scoped_backend

    started = await _gql(client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["startCase"]["id"]
    send = await _gql(
        client, SEND, {"id": sid, "text": "When did the infections start?"}
    )
    assert send["sendMessage"]["branch"] == "PARENT"

    resp = await client.get(f"/sse/parent/{sid}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    deltas = [
        json.loads(line[len("data: "):])["delta"]
        for line in resp.text.splitlines()
        if line.startswith("data: ") and "delta" in line
    ]
    assert deltas == llm.stream_chunks
    assert 'data: {"done": true}' in resp.text

    sess = (await _gql(client, SESSION, {"id": sid}))["session"]
    parent_msgs = [m for m in sess["messages"] if m["type"] == "parent"]
    assert len(parent_msgs) == 1
    assert parent_msgs[0]["text"] == "He started at six months."

    second = await client.get(f"/sse/parent/{sid}")
    assert second.status_code == 409


async def test_db_path_sse_unknown_session_404(
    request_scoped_backend, client, admin_principal
):
    from tests.conftest import auth_cookies

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies=auth_cookies(admin_principal),
    ) as ac:
        resp = await ac.get("/sse/parent/does-not-exist")
    assert resp.status_code == 404


async def test_default_path_has_no_factory():
    assert runtime.has_service_factory() is False
