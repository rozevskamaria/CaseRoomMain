from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings, get_settings


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolRunResult:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    refused: bool = False

    @property
    def first_tool_call(self) -> ToolCall | None:
        return self.tool_calls[0] if self.tool_calls else None


class LLMClient:
    def __init__(self, client: Any | None = None, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client
        self.model: str = self._settings.ANTHROPIC_MODEL

    @property
    def client(self) -> Any:
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._settings.ANTHROPIC_API_KEY)
        return self._client

    async def generate(
        self,
        system: str,
        messages: Sequence[dict[str, str]],
        max_tokens: int,
    ) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""

    async def generate_structured(
        self,
        system: str,
        messages: Sequence[dict[str, str]],
        schema: dict[str, Any],
        max_tokens: int,
    ) -> dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        for block in response.content:
            if block.type == "text":
                return json.loads(block.text)
        return {}

    async def generate_with_tools(
        self,
        system: str,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]],
        max_tokens: int = 512,
        max_iterations: int = 5,
    ) -> ToolRunResult:
        convo = list(messages)
        text = ""
        for _ in range(max_iterations):
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=convo,
                tools=list(tools),
                tool_choice={"type": "any", "disable_parallel_tool_use": True},
            )
            if getattr(response, "stop_reason", None) == "refusal":
                return ToolRunResult(text="", tool_calls=[], refused=True)
            if getattr(response, "stop_reason", None) == "pause_turn":
                convo.append({"role": "assistant", "content": response.content})
                continue
            calls: list[ToolCall] = []
            for block in response.content:
                if block.type == "tool_use":
                    calls.append(
                        ToolCall(id=block.id, name=block.name, input=dict(block.input))
                    )
                elif block.type == "text":
                    text = block.text
            return ToolRunResult(text=text, tool_calls=calls, refused=False)
        return ToolRunResult(text=text, tool_calls=[], refused=False)

    async def stream(
        self,
        system: str,
        messages: Sequence[dict[str, str]],
        max_tokens: int,
    ) -> AsyncIterator[str]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
