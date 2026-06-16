from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.runtime import get_llm_client, get_session_service

router = APIRouter()

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


@router.get("/sse/parent/{session_id}")
async def sse_parent(session_id: str) -> StreamingResponse:
    service = get_session_service()
    session = service.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session")

    pending = session.pending_parent
    if pending is None or pending.branch != "parent":
        raise HTTPException(status_code=409, detail="No pending parent reply")

    session.pending_parent = None
    llm = get_llm_client()

    async def event_stream() -> AsyncIterator[str]:
        chunks: list[str] = []
        async for delta in llm.stream(
            pending.system or "",
            pending.messages or [],
            pending.max_tokens or _PARENT_MAX_TOKENS,
        ):
            chunks.append(delta)
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        service.append_parent_reply(session, "".join(chunks))
        yield "data: {\"done\": true}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
