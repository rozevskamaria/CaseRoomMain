from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.auth.email import EmailService
from app.auth.stores import (
    MagicLinkStore,
    RateLimiter,
    SessionStore,
    UserStore,
)
from app.core.config import Settings
from app.models.user import User, UserRole, UserStatus
from app.services.jobs import JobQueue
from app.workers.jobs import SEND_MAGIC_LINK

_DIGITS6 = re.compile(r"^\d{6}$")

Background = Callable[[Callable[[], Awaitable[None]]], None]


_background_tasks: set = set()


def _run_now(coro_factory: Callable[[], Awaitable[None]]) -> None:
    import asyncio

    task = asyncio.ensure_future(coro_factory())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


class _InlineEmailQueue:
    def __init__(self, email: EmailService) -> None:
        self._email = email

    async def enqueue(self, job_name: str, **kwargs):
        if job_name == SEND_MAGIC_LINK:
            await self._email.send_magic_link(kwargs["to_email"], kwargs["link"])


@dataclass
class AuthResult:
    ok: bool = True


@dataclass
class ConsumeResult:
    ok: bool
    session_id: str | None = None
    user: User | None = None
    reason: str | None = None


class AuthService:
    def __init__(
        self,
        users: UserStore,
        sessions: SessionStore,
        links: MagicLinkStore,
        limiter: RateLimiter,
        email: EmailService,
        settings: Settings,
        background: Background | None = None,
        queue: JobQueue | None = None,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._links = links
        self._limiter = limiter
        self._email = email
        self._settings = settings
        self._background = background or _run_now
        self._queue = queue or self._default_queue()

    def _default_queue(self) -> JobQueue:
        return _InlineEmailQueue(self._email)

    def _link_for(self, token: str) -> str:
        return f"{self._settings.PUBLIC_BASE_URL}/auth/verify?token={token}"

    async def _send_login_link(self, user: User, email: str) -> None:
        token = await self._links.issue(str(user.id), "login")
        await self._queue.enqueue(
            SEND_MAGIC_LINK, to_email=email, link=self._link_for(token)
        )

    def _schedule_login_email(self, user: User, login_name: str) -> None:
        async def _task() -> None:
            email = await self._users.decrypt_email(user) or (
                f"{login_name}@rsu.edu.lv"
            )
            await self._send_login_link(user, email)

        self._background(_task)

    def _schedule_staff_email(self, user: User, email: str) -> None:
        async def _task() -> None:
            await self._send_login_link(user, email)

        self._background(_task)

    def _schedule_register(self, login_name: str, full_name: str | None) -> None:
        async def _task() -> None:
            user = await self._users.get_by_login_hash(login_name)
            if user is None:
                user = await self._users.create_student(login_name, full_name)
            if user.status == UserStatus.disabled:
                return
            purpose = "register" if user.status == UserStatus.invited else "login"
            token = await self._links.issue(str(user.id), purpose)
            email = f"{login_name}@rsu.edu.lv"
            await self._queue.enqueue(
                SEND_MAGIC_LINK, to_email=email, link=self._link_for(token)
            )

        self._background(_task)

    async def request_link(self, login_name: str, ip: str | None) -> AuthResult:
        s = self._settings
        ip = ip or "unknown"
        ip_ok = await self._limiter.allow(
            "reqlink",
            ip,
            s.RATE_LIMIT_REQUEST_LINK_PER_IP,
            s.RATE_LIMIT_REQUEST_LINK_WINDOW_SECONDS,
        )
        subject_ok = await self._limiter.allow(
            "reqlink",
            login_name,
            s.RATE_LIMIT_REQUEST_LINK_PER_SUBJECT,
            s.RATE_LIMIT_REQUEST_LINK_WINDOW_SECONDS,
        )
        if not (ip_ok and subject_ok):
            return AuthResult()
        if not _DIGITS6.match(login_name):
            return AuthResult()
        user = await self._users.get_by_login_hash(login_name)
        if user is not None and user.status != UserStatus.disabled:
            self._schedule_login_email(user, login_name)
        return AuthResult()

    async def register_student(
        self, login_name: str, full_name: str | None, ip: str | None
    ) -> AuthResult:
        s = self._settings
        ip = ip or "unknown"
        ip_ok = await self._limiter.allow(
            "register",
            ip,
            s.RATE_LIMIT_REGISTER_PER_IP,
            s.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        )
        subject_ok = await self._limiter.allow(
            "register",
            login_name,
            s.RATE_LIMIT_REGISTER_PER_SUBJECT,
            s.RATE_LIMIT_REGISTER_WINDOW_SECONDS,
        )
        if not (ip_ok and subject_ok):
            return AuthResult()
        if not _DIGITS6.match(login_name):
            return AuthResult()
        await self._users.get_by_login_hash(login_name)
        self._schedule_register(login_name, full_name)
        return AuthResult()

    async def consume_link(
        self, token: str, ip: str | None = None
    ) -> ConsumeResult:
        s = self._settings
        allowed = await self._limiter.allow(
            "consume",
            ip or "unknown",
            s.RATE_LIMIT_CONSUME_PER_IP,
            s.RATE_LIMIT_CONSUME_WINDOW_SECONDS,
        )
        if not allowed:
            return ConsumeResult(ok=False, reason="rate_limited")
        record = await self._links.consume(token)
        if record is None:
            return ConsumeResult(ok=False, reason="expired")
        user = await self._users.get(record.user_id)
        if user is None or user.status == UserStatus.disabled:
            return ConsumeResult(ok=False, reason="expired")
        if user.status == UserStatus.invited:
            await self._users.set_status(user.id, UserStatus.active)
            await self._users.stamp_consent(
                user.id, self._settings.CONSENT_VERSION
            )
            user.status = UserStatus.active
        session_id = await self._sessions.create(str(user.id))
        return ConsumeResult(ok=True, session_id=session_id, user=user)

    async def logout(self, session_id: str | None) -> AuthResult:
        if session_id:
            await self._sessions.revoke(session_id)
        return AuthResult()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._sessions.revoke_all_for_user(str(user_id))

    async def create_staff(
        self, login_name: str, email: str, full_name: str | None, role: UserRole
    ) -> User:
        user = await self._users.create_staff(login_name, email, full_name, role)
        self._schedule_staff_email(user, email)
        return user
