from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.core.config import Settings, get_settings


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
