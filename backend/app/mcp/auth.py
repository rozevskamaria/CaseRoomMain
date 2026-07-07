from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.models.user import UserRole


@dataclass(frozen=True)
class ResearchPrincipal:
    kind: str = "mcp_research"
    role: UserRole = UserRole.admin
    read_only: bool = True


def _present_tokens(token_config: str) -> set[str]:
    return {t.strip() for t in token_config.split(",") if t.strip()}


def authenticate_mcp(authorization: str | None, token_config: str) -> bool:
    tokens = _present_tokens(token_config)
    if not tokens:
        return False
    if not authorization or not authorization.startswith("Bearer "):
        return False
    presented = authorization[len("Bearer ") :].strip()
    if not presented:
        return False
    return any(secrets.compare_digest(presented, t) for t in tokens)


class MCPAuthMiddleware:
    def __init__(self, app, token_config: str) -> None:
        self._app = app
        self._token_config = token_config

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        authorization = None
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                authorization = value.decode("latin-1")
                break
        if not authenticate_mcp(authorization, self._token_config):
            await _send_401(send)
            return
        await self._app(scope, receive, send)


async def _send_401(send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send(
        {
            "type": "http.response.body",
            "body": b"unauthorized",
        }
    )
