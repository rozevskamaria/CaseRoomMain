from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.api import runtime
from app.api.runtime import get_llm_client, get_session_service
from app.auth import runtime as auth_runtime
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.models.user import UserRole

router = APIRouter()


def _cookie_sid(request: Request) -> str | None:
    return request.cookies.get(get_settings().SESSION_COOKIE_NAME)


def _active(user):
    from app.models.user import UserStatus

    if user is None or user.status != UserStatus.active:
        return None
    return user


def _enforce_owner(user, owner_id: str | None) -> None:
    user = _active(user)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.role == UserRole.admin:
        return
    if owner_id is not None and str(owner_id) == str(user.id):
        return
    raise HTTPException(status_code=403, detail="Forbidden")

_TICK_COUNT = 3
_TICK_DELAY_SECONDS = 0.01

_PARENT_MAX_TOKENS = 300


async def _ping_event_stream() -> AsyncIterator[str]:
    for n in range(_TICK_COUNT):
        yield f'data: {{"tick": {n}}}\n\n'
        await asyncio.sleep(_TICK_DELAY_SECONDS)


@router.get("/sse/ping")
async def sse_ping() -> StreamingResponse:
    return StreamingResponse(_ping_event_stream(), media_type="text/event-stream")


def _pending_parent_request(events: list) -> dict | None:
    pending: dict | None = None
    for record in sorted(events, key=lambda e: e.seq):
        if record.type == "ParentReplyRequested":
            pending = record.data
        elif record.type == "ParentReplyAppended":
            pending = None
    return pending


@router.get("/sse/parent/{session_id}")
async def sse_parent(session_id: str, request: Request) -> StreamingResponse:
    sid = _cookie_sid(request)

    if not runtime.has_service_factory():
        service = get_session_service()
        user = await auth_runtime.resolve_current_user(sid, None)
        owner_id = await service.get_attempt_owner(session_id)
        _enforce_owner(user, owner_id)
        events = await service._store.load_events(session_id)
        if not events:
            raise HTTPException(status_code=404, detail="Unknown session")
        pending = _pending_parent_request(events)
        if pending is None:
            raise HTTPException(status_code=409, detail="No pending parent reply")

        llm = get_llm_client()

        async def event_stream() -> AsyncIterator[str]:
            chunks: list[str] = []
            async for delta in llm.stream(
                pending.get("system") or "",
                pending.get("history") or [],
                pending.get("max_tokens") or _PARENT_MAX_TOKENS,
            ):
                chunks.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            await service.append_parent_reply(session_id, "".join(chunks))
            yield 'data: {"done": true}\n\n'

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    session_factory = get_sessionmaker()
    session = session_factory()
    service = runtime.build_request_service(session)
    token = runtime.use_request_service(service)
    try:
        user = await auth_runtime.resolve_current_user(sid, session)
        owner_id = await service.get_attempt_owner(session_id)
        _enforce_owner(user, owner_id)
        events = await service._store.load_events(session_id)
        if not events:
            raise HTTPException(status_code=404, detail="Unknown session")
        pending = _pending_parent_request(events)
        if pending is None:
            raise HTTPException(status_code=409, detail="No pending parent reply")
    except BaseException:
        await session.close()
        raise
    finally:
        runtime.reset_request_service(token)

    llm = get_llm_client()

    async def db_event_stream() -> AsyncIterator[str]:
        try:
            chunks: list[str] = []
            async for delta in llm.stream(
                pending.get("system") or "",
                pending.get("history") or [],
                pending.get("max_tokens") or _PARENT_MAX_TOKENS,
            ):
                chunks.append(delta)
                yield f"data: {json.dumps({'delta': delta})}\n\n"
            await service.append_parent_reply(session_id, "".join(chunks))
            await session.commit()
            yield 'data: {"done": true}\n\n'
        finally:
            await session.close()

    return StreamingResponse(db_event_stream(), media_type="text/event-stream")
