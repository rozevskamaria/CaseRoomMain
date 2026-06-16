from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.core.config import Settings
from app.llm.client import LLMClient


class FakeTextStream:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        return self._aiter()

    async def _aiter(self):
        for chunk in self._chunks:
            yield chunk


class FakeStreamContext:
    def __init__(self, chunks):
        self.text_stream = FakeTextStream(chunks)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_client(create=None, stream=None):
    messages = SimpleNamespace(create=create, stream=stream)
    return SimpleNamespace(messages=messages)


async def test_generate_returns_text_and_passes_callclaude_body():
    block = SimpleNamespace(type="text", text="pong-reply")
    response = SimpleNamespace(content=[block])
    create = AsyncMock(return_value=response)
    fake = make_client(create=create)
    llm = LLMClient(client=fake)

    system = "you are a parent"
    messages = [{"role": "user", "content": "hello"}]
    result = await llm.generate(system, messages, 300)

    assert result == "pong-reply"
    create.assert_awaited_once_with(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system,
        messages=messages,
    )


async def test_generate_returns_empty_string_when_no_text_block():
    block = SimpleNamespace(type="tool_use")
    response = SimpleNamespace(content=[block])
    fake = make_client(create=AsyncMock(return_value=response))
    llm = LLMClient(client=fake)

    result = await llm.generate("sys", [{"role": "user", "content": "hi"}], 300)

    assert result == ""


async def test_stream_yields_text_deltas():
    def stream(**kwargs):
        return FakeStreamContext(["a", "b", "c"])

    fake = make_client(stream=stream)
    llm = LLMClient(client=fake)

    joined = "".join(
        [chunk async for chunk in llm.stream("sys", [{"role": "user", "content": "hi"}], 300)]
    )

    assert joined == "abc"


async def test_model_read_from_injected_settings():
    settings = Settings(ANTHROPIC_MODEL="claude-sonnet-4-6", ANTHROPIC_API_KEY="")
    llm = LLMClient(client=make_client(), settings=settings)
    assert llm.model == settings.ANTHROPIC_MODEL
