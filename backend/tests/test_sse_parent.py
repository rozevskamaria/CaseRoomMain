from __future__ import annotations

import itertools
import json

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.runtime as runtime
from app.main import app
from app.services import SessionService


class FakeLLMClient:
    def __init__(self):
        self.stream_chunks = ["Infections ", "started ", "at six months."]
        self.stream_calls = []

    async def generate(self, system, messages, max_tokens):
        return "unused"

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
async def http_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _prepare_parent_session():
    service = runtime.get_session_service()
    session = service.start_case("xla", "practice")
    result = service.send_message(session, "When did the infections start?")
    assert result.branch == "parent"
    session.pending_parent = result
    return session


def _deltas(body):
    out = []
    for line in body.splitlines():
        if line.startswith("data: "):
            payload = json.loads(line[len("data: "):])
            if "delta" in payload:
                out.append(payload["delta"])
    return out


async def test_sse_parent_streams_and_appends_reply(fake_llm, http_client):
    session = _prepare_parent_session()

    resp = await http_client.get(f"/sse/parent/{session.id}")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    deltas = _deltas(resp.text)
    assert deltas == ["Infections ", "started ", "at six months."]
    assert 'data: {"done": true}' in resp.text

    assert fake_llm.stream_calls[0]["max_tokens"] == 300
    assert fake_llm.stream_calls[0]["system"] == _expected_parent_prompt()

    parent_msgs = [m for m in session.messages if m.type == "parent"]
    assert len(parent_msgs) == 1
    assert parent_msgs[0].text == "Infections started at six months."
    assert session.pending_parent is None


def _expected_parent_prompt():
    from app.content.cases import get_case

    return get_case("xla").parent_prompt


async def test_sse_parent_unknown_session_404(fake_llm, http_client):
    resp = await http_client.get("/sse/parent/does-not-exist")
    assert resp.status_code == 404


async def test_sse_parent_no_pending_returns_409(fake_llm, http_client):
    service = runtime.get_session_service()
    session = service.start_case("xla", "practice")

    resp = await http_client.get(f"/sse/parent/{session.id}")
    assert resp.status_code == 409


async def test_sse_parent_consumed_once(fake_llm, http_client):
    session = _prepare_parent_session()

    first = await http_client.get(f"/sse/parent/{session.id}")
    assert first.status_code == 200

    second = await http_client.get(f"/sse/parent/{session.id}")
    assert second.status_code == 409


async def test_sse_ping_still_works(fake_llm, http_client):
    resp = await http_client.get("/sse/ping")
    assert resp.status_code == 200
    assert 'data: {"tick": 0}' in resp.text
