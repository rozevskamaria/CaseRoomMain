from __future__ import annotations

from app.llm.client import LLMClient
from app.services import SessionService

_llm_client: LLMClient | None = None
_session_service: SessionService | None = None


def set_llm_client(client: LLMClient) -> None:
    global _llm_client, _session_service
    _llm_client = client
    _session_service = SessionService(client)


def set_session_service(service: SessionService) -> None:
    global _session_service
    _session_service = service


def reset() -> None:
    global _llm_client, _session_service
    _llm_client = None
    _session_service = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService(get_llm_client())
    return _session_service
