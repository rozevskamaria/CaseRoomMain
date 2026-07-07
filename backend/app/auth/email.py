from __future__ import annotations

import logging
from typing import Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger("caseroom.email")


class EmailService(Protocol):
    async def send_magic_link(self, to_email: str, link: str) -> None: ...


def _subject_and_html(link: str) -> tuple[str, str]:
    subject = "Your CaseRoom sign-in link"
    html = (
        "<p>Click to sign in to CaseRoom:</p>"
        f'<p><a href="{link}">{link}</a></p>'
        "<p>This link expires in 15 minutes and can be used once.</p>"
    )
    return subject, html


class DevEmailService:
    async def send_magic_link(self, to_email: str, link: str) -> None:
        logger.info("magic link for %s: %s", to_email, link)


class ResendEmailService:
    def __init__(self, api_key: str, sender: str) -> None:
        self._api_key = api_key
        self._sender = sender

    async def send_magic_link(self, to_email: str, link: str) -> None:
        subject, html = _subject_and_html(link)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "from": self._sender,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            resp.raise_for_status()


def get_email_service() -> EmailService:
    settings = get_settings()
    if settings.RESEND_API_KEY:
        return ResendEmailService(settings.RESEND_API_KEY, settings.RESEND_SENDER)
    return DevEmailService()
