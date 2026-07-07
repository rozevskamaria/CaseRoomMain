from __future__ import annotations

from app.mcp.auth import MCPAuthMiddleware, authenticate_mcp

TOKEN = "secret-research-token"


def test_authenticate_unset_token_rejects_everything():
    assert authenticate_mcp("Bearer anything", "") is False
    assert authenticate_mcp(None, "") is False


def test_authenticate_missing_or_malformed_header():
    assert authenticate_mcp(None, TOKEN) is False
    assert authenticate_mcp("", TOKEN) is False
    assert authenticate_mcp("Token " + TOKEN, TOKEN) is False
    assert authenticate_mcp("Bearer ", TOKEN) is False
    assert authenticate_mcp("Bearer wrong", TOKEN) is False


def test_authenticate_valid_token():
    assert authenticate_mcp(f"Bearer {TOKEN}", TOKEN) is True


def test_authenticate_multi_token_config():
    assert authenticate_mcp("Bearer second", "first, second") is True
    assert authenticate_mcp("Bearer third", "first, second") is False


class _Recorder:
    def __init__(self) -> None:
        self.called = False

    async def __call__(self, scope, receive, send):
        self.called = True
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send({"type": "http.response.body", "body": b"ok"})


async def _drive(app, method="POST", headers=None):
    headers = headers or []
    scope = {
        "type": "http",
        "method": method,
        "path": "/mcp",
        "headers": headers,
    }
    sent: list[dict] = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in sent if m["type"] == "http.response.start")
    return status, sent


def _bearer(token: str):
    return [(b"authorization", f"Bearer {token}".encode())]


async def test_middleware_rejects_missing_bearer():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, TOKEN)
    status, _ = await _drive(mw, headers=[])
    assert status == 401
    assert inner.called is False


async def test_middleware_rejects_wrong_bearer():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, TOKEN)
    status, _ = await _drive(mw, headers=_bearer("nope"))
    assert status == 401
    assert inner.called is False


async def test_middleware_allows_valid_bearer():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, TOKEN)
    status, _ = await _drive(mw, headers=_bearer(TOKEN))
    assert status == 200
    assert inner.called is True


async def test_middleware_enforces_on_every_request_after_valid_one():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, TOKEN)
    status_ok, _ = await _drive(mw, headers=_bearer(TOKEN))
    assert status_ok == 200
    inner.called = False
    status_followup, _ = await _drive(mw, method="POST", headers=[])
    assert status_followup == 401
    assert inner.called is False


async def test_middleware_enforces_on_get_event_stream():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, TOKEN)
    status, _ = await _drive(mw, method="GET", headers=[])
    assert status == 401
    assert inner.called is False
    status_ok, _ = await _drive(mw, method="GET", headers=_bearer(TOKEN))
    assert status_ok == 200


async def test_middleware_unset_token_rejects_valid_looking_request():
    inner = _Recorder()
    mw = MCPAuthMiddleware(inner, "")
    status, _ = await _drive(mw, headers=_bearer(TOKEN))
    assert status == 401
    assert inner.called is False


def test_mcp_not_mounted_when_disabled(monkeypatch):
    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("MCP_ENABLED", "false")
    get_settings.cache_clear()
    app = create_app()
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/mcp" not in paths
    get_settings.cache_clear()


def test_mcp_mounted_when_enabled(monkeypatch):
    from app.core.config import get_settings
    from app.main import create_app

    monkeypatch.setenv("MCP_ENABLED", "true")
    monkeypatch.setenv("MCP_RESEARCH_TOKEN", TOKEN)
    monkeypatch.setenv("RESEARCH_PSEUDONYM_PEPPER", "distinct-research-pepper")
    get_settings.cache_clear()
    app = create_app()
    mounted = any(getattr(r, "path", "").startswith("/mcp") for r in app.routes)
    assert mounted
    get_settings.cache_clear()
