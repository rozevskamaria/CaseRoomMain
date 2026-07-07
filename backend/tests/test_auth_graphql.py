from __future__ import annotations

import itertools

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.runtime as runtime
from app.main import app
from app.services import SessionService
from tests.conftest import auth_cookies


class FakeLLMClient:
    def __init__(self):
        self.stream_chunks = ["Hello", " parent"]

    async def generate(self, system, messages, max_tokens):
        return "canned"

    async def generate_structured(self, system, messages, schema, max_tokens):
        return {}

    async def stream(self, system, messages, max_tokens):
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
async def anon_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _client_with(principal):
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies=auth_cookies(principal),
    )


async def _post(client, query, variables=None):
    resp = await client.post(
        "/graphql", json={"query": query, "variables": variables or {}}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


START = """
mutation Start($caseId: String!, $mode: String!) {
  startCase(caseId: $caseId, mode: $mode) { id }
}
"""


async def _start_owned_attempt(fake_llm, principal) -> str:
    async with _client_with(principal) as client:
        payload = await _post(
            client, START, {"caseId": "xla", "mode": "practice"}
        )
    assert "errors" not in payload, payload
    return payload["data"]["startCase"]["id"]


async def test_start_case_requires_auth(fake_llm, anon_client):
    payload = await _post(anon_client, START, {"caseId": "xla", "mode": "practice"})
    assert payload.get("errors")
    assert "Authentication required" in payload["errors"][0]["message"]


async def test_case_query_requires_auth(fake_llm, anon_client):
    payload = await _post(
        anon_client,
        "query Q($id: String!) { case(id: $id) { id } }",
        {"id": "xla"},
    )
    assert payload.get("errors")


async def test_me_null_when_unauthenticated(fake_llm, anon_client):
    payload = await _post(anon_client, "query { me { id } }")
    assert "errors" not in payload, payload
    assert payload["data"]["me"] is None


async def test_send_message_unauthenticated_rejected(fake_llm, student_principal):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon:
        payload = await _post(
            anon,
            "mutation M($id: String!) { sendMessage(sessionId: $id, text: \"hi\") { branch } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Authentication required" in payload["errors"][0]["message"]


async def test_non_owner_student_cannot_send_message(
    fake_llm, student_principal, other_student
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(other_student) as client:
        payload = await _post(
            client,
            "mutation M($id: String!) { sendMessage(sessionId: $id, text: \"hi\") { branch } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]


async def test_non_owner_student_cannot_query_session(
    fake_llm, student_principal, other_student
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(other_student) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]


async def test_non_owner_cannot_reach_nested_messages(
    fake_llm, student_principal, other_student
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(other_student) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { messages { text } } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]


async def test_non_owner_cannot_reach_attempt_events(
    fake_llm, student_principal, other_student
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(other_student) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { attempt(id: $id) { events { __typename } } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]


async def test_disabled_user_rejected(fake_llm, student_principal, disabled_student):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(disabled_student) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Authentication required" in payload["errors"][0]["message"]


async def test_staff_cannot_read_other_students_attempt(
    fake_llm, student_principal, staff_principal
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(staff_principal) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id } }",
            {"id": sid},
        )
    assert payload.get("errors")
    assert "Forbidden" in payload["errors"][0]["message"]


async def test_staff_can_read_their_own_attempt(fake_llm, staff_principal):
    sid = await _start_owned_attempt(fake_llm, staff_principal)
    async with _client_with(staff_principal) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id } }",
            {"id": sid},
        )
    assert "errors" not in payload, payload
    assert payload["data"]["session"]["id"] == sid


async def test_admin_can_read_other_students_attempt(
    fake_llm, student_principal, admin_principal
):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(admin_principal) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id } }",
            {"id": sid},
        )
    assert "errors" not in payload, payload
    assert payload["data"]["session"]["id"] == sid


async def test_owner_can_play(fake_llm, student_principal):
    sid = await _start_owned_attempt(fake_llm, student_principal)
    async with _client_with(student_principal) as client:
        payload = await _post(
            client,
            "query Q($id: String!) { session(id: $id) { id phase } }",
            {"id": sid},
        )
    assert "errors" not in payload, payload
    assert payload["data"]["session"]["id"] == sid


async def test_create_staff_requires_admin(fake_llm, student_principal):
    async with _client_with(student_principal) as client:
        payload = await _post(
            client,
            'mutation { createStaff(loginName: "tutor9", email: "t9@rsu.edu.lv", '
            'fullName: "T9", role: "staff") { id } }',
        )
    assert payload.get("errors")
    assert "Admin only" in payload["errors"][0]["message"]


async def test_sse_unauthenticated_401(fake_llm, student_principal):
    sid = await _prepare_pending(fake_llm, student_principal)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as anon:
        resp = await anon.get(f"/sse/parent/{sid}")
    assert resp.status_code == 401


async def test_sse_non_owner_403(fake_llm, student_principal, other_student):
    sid = await _prepare_pending(fake_llm, student_principal)
    async with _client_with(other_student) as client:
        resp = await client.get(f"/sse/parent/{sid}")
    assert resp.status_code == 403


async def test_sse_owner_200(fake_llm, student_principal):
    sid = await _prepare_pending(fake_llm, student_principal)
    async with _client_with(student_principal) as client:
        resp = await client.get(f"/sse/parent/{sid}")
    assert resp.status_code == 200


async def test_sse_disabled_user_rejected(
    fake_llm, student_principal, disabled_student
):
    sid = await _prepare_pending(fake_llm, student_principal)
    async with _client_with(disabled_student) as client:
        resp = await client.get(f"/sse/parent/{sid}")
    assert resp.status_code == 401


async def test_dev_login_mints_real_session_and_owns_attempt(fake_llm, anon_client):
    payload = await _post(
        anon_client,
        'mutation { devLogin(loginName: "909090") { ok reason } }',
    )
    assert payload["data"]["devLogin"]["ok"] is True

    me = await _post(anon_client, "query { me { id loginName status } }")
    assert me["data"]["me"]["loginName"] == "909090"
    assert me["data"]["me"]["status"] == "active"

    started = await _post(anon_client, START, {"caseId": "xla", "mode": "practice"})
    sid = started["data"]["startCase"]["id"]
    owner = await runtime.get_session_service().get_attempt_owner(sid)
    assert str(owner) == me["data"]["me"]["id"]


async def test_dev_login_disabled_in_production(fake_llm, anon_client, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("APP_ENV", "production")
    get_settings.cache_clear()
    try:
        payload = await _post(
            anon_client,
            'mutation { devLogin(loginName: "111222") { ok reason } }',
        )
        assert payload["data"]["devLogin"]["ok"] is False
        assert payload["data"]["devLogin"]["reason"] == "disabled"
    finally:
        get_settings.cache_clear()


async def _prepare_pending(fake_llm, principal) -> str:
    service = runtime.get_session_service()
    proj = await service.start_case(
        "xla", "practice", student_id=principal["user_id"]
    )
    result, _ = await service.send_message(proj.id, "When did it start?")
    assert result.branch == "parent"
    return proj.id


async def test_full_auth_flow_register_consume_me_and_ownership(fake_llm, anon_client):
    register = await _post(
        anon_client,
        'mutation { registerStudent(loginName: "424242", fullName: "Flow Student") { ok } }',
    )
    assert register["data"]["registerStudent"]["ok"] is True

    from app.auth import runtime as auth_runtime

    store = auth_runtime.get_user_store(None)
    user = await store.get_by_login_hash("424242")
    assert user is not None
    token = await auth_runtime.build_auth_service(None)._links.issue(  # noqa: SLF001
        str(user.id), "register"
    )

    consume = await _post(
        anon_client,
        "mutation C($t: String!) { consumeMagicLink(token: $t) { ok reason } }",
        {"t": token},
    )
    assert consume["data"]["consumeMagicLink"]["ok"] is True

    me = await _post(anon_client, "query { me { id loginName role status } }")
    assert me["data"]["me"]["loginName"] == "424242"
    assert me["data"]["me"]["role"] == "student"
    assert me["data"]["me"]["status"] == "active"

    started = await _post(
        anon_client, START, {"caseId": "xla", "mode": "practice"}
    )
    sid = started["data"]["startCase"]["id"]
    owner = await runtime.get_session_service().get_attempt_owner(sid)
    assert str(owner) == me["data"]["me"]["id"]

    play = await _post(
        anon_client,
        "query Q($id: String!) { session(id: $id) { id } }",
        {"id": sid},
    )
    assert play["data"]["session"]["id"] == sid

    logout = await _post(anon_client, "mutation { logout { ok } }")
    assert logout["data"]["logout"]["ok"] is True

    after = await _post(anon_client, "query { me { id } }")
    assert after["data"]["me"] is None
