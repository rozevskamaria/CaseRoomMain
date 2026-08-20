from __future__ import annotations

from app.auth.service import AuthService
from app.auth.stores import (
    InMemoryMagicLinkStore,
    InMemoryRateLimiter,
    InMemorySessionStore,
    InMemoryUserStore,
)
from app.core.config import Settings
from app.models.user import UserRole, UserStatus


class RecordingEmail:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_magic_link(self, to_email: str, link: str) -> None:
        self.sent.append((to_email, link))

    def last_token(self) -> str:
        link = self.sent[-1][1]
        return link.rsplit("token=", 1)[1]


class InlineBackground:
    def __init__(self) -> None:
        self._tasks: list = []

    def __call__(self, coro_factory) -> None:
        self._tasks.append(coro_factory)

    async def drain(self) -> None:
        while self._tasks:
            task = self._tasks.pop(0)
            await task()


def _settings() -> Settings:
    return Settings(
        PUBLIC_BASE_URL="https://caseroom.test",
        CONSENT_VERSION="v1",
    )


def _make_service(
    users: InMemoryUserStore | None = None,
    email: RecordingEmail | None = None,
    background: InlineBackground | None = None,
):
    users = users or InMemoryUserStore()
    sessions = InMemorySessionStore()
    links = InMemoryMagicLinkStore()
    limiter = InMemoryRateLimiter()
    email = email or RecordingEmail()
    background = background or InlineBackground()
    service = AuthService(
        users=users,
        sessions=sessions,
        links=links,
        limiter=limiter,
        email=email,
        settings=_settings(),
        background=background,
    )
    return service, users, sessions, links, limiter, email, background


async def test_register_then_consume_creates_active_session():
    service, users, sessions, _links, _lim, email, bg = _make_service()

    result = await service.register_student("123456", "Test Student", "1.1.1.1")
    assert result.ok is True
    assert email.sent == []

    await bg.drain()
    assert len(email.sent) == 1
    assert email.sent[0][0] == "123456@rsu.edu.lv"

    user = await users.get_by_login_hash("123456")
    assert user is not None
    assert user.status == UserStatus.invited

    consume = await service.consume_link(email.last_token())
    assert consume.ok is True
    assert consume.session_id is not None
    assert consume.user is not None
    assert consume.user.status == UserStatus.active

    resolved = await sessions.resolve(consume.session_id)
    assert resolved == str(user.id)


async def test_existing_user_login_flow():
    service, users, _sessions, _links, _lim, email, bg = _make_service()
    await users.create_student("654321", "Existing")

    result = await service.request_link("654321", "1.1.1.1")
    assert result.ok is True
    await bg.drain()
    assert len(email.sent) == 1

    consume = await service.consume_link(email.last_token())
    assert consume.ok is True
    assert consume.user.status == UserStatus.active


async def test_consume_is_single_use():
    service, _users, _sessions, _links, _lim, email, bg = _make_service()
    await service.register_student("111111", None, "1.1.1.1")
    await bg.drain()
    token = email.last_token()

    first = await service.consume_link(token)
    assert first.ok is True

    second = await service.consume_link(token)
    assert second.ok is False
    assert second.reason == "expired"


async def test_consume_invalid_and_expired_token():
    service, _users, _sessions, links, _lim, _email, _bg = _make_service()

    bad = await service.consume_link("does-not-exist")
    assert bad.ok is False
    assert bad.reason == "expired"

    links._ttl = -1
    token = await links.issue("00000000-0000-0000-0000-000000000000", "login")
    expired = await service.consume_link(token)
    assert expired.ok is False
    assert expired.reason == "expired"


async def test_rate_limit_triggers_generic_response():
    settings = Settings(
        RATE_LIMIT_REQUEST_LINK_PER_IP=2,
        RATE_LIMIT_REQUEST_LINK_PER_SUBJECT=2,
        RATE_LIMIT_REQUEST_LINK_WINDOW_SECONDS=600,
    )
    users = InMemoryUserStore()
    await users.create_student("222222", None)
    email = RecordingEmail()
    bg = InlineBackground()
    service = AuthService(
        users=users,
        sessions=InMemorySessionStore(),
        links=InMemoryMagicLinkStore(),
        limiter=InMemoryRateLimiter(),
        email=email,
        settings=settings,
        background=bg,
    )

    for _ in range(2):
        assert (await service.request_link("222222", "9.9.9.9")).ok is True
    blocked = await service.request_link("222222", "9.9.9.9")
    assert blocked.ok is True

    await bg.drain()
    assert len(email.sent) == 2


async def test_no_account_enumeration_identical_results():
    service, users, _sessions, _links, _lim, _email, _bg = _make_service()
    await users.create_student("333333", None)

    existing = await service.request_link("333333", "1.1.1.1")
    missing = await service.request_link("999999", "1.1.1.1")
    assert existing == missing

    reg_existing = await service.register_student("333333", None, "2.2.2.2")
    reg_new = await service.register_student("444444", None, "2.2.2.2")
    assert reg_existing == reg_new


async def test_consent_stamped_on_first_activation_regardless_of_purpose():
    service, users, _sessions, links, _lim, _email, _bg = _make_service()
    user = await users.create_student("555555", None)
    assert user.consent_at is None

    token = await links.issue(str(user.id), "login")
    consume = await service.consume_link(token)
    assert consume.ok is True

    refreshed = await users.get(str(user.id))
    assert refreshed.status == UserStatus.active
    assert refreshed.consent_at is not None
    assert refreshed.consent_version == "v1"


async def test_logout_revokes_session():
    service, _users, sessions, _links, _lim, email, bg = _make_service()
    await service.register_student("666666", None, "1.1.1.1")
    await bg.drain()
    consume = await service.consume_link(email.last_token())
    sid = consume.session_id
    assert await sessions.resolve(sid) is not None

    await service.logout(sid)
    assert await sessions.resolve(sid) is None


async def test_revoke_all_for_user_clears_every_session():
    service, users, sessions, links, _lim, email, bg = _make_service()
    await service.register_student("777777", None, "1.1.1.1")
    await bg.drain()
    user = await users.get_by_login_hash("777777")

    first = await service.consume_link(email.last_token())
    second_token = await links.issue(str(user.id), "login")
    second = await service.consume_link(second_token)

    assert await sessions.resolve(first.session_id) is not None
    assert await sessions.resolve(second.session_id) is not None

    await service.revoke_all_for_user(str(user.id))
    assert await sessions.resolve(first.session_id) is None
    assert await sessions.resolve(second.session_id) is None


async def test_disabled_user_consume_rejected():
    service, users, _sessions, links, _lim, _email, _bg = _make_service()
    user = await users.create_student("888888", None)
    await users.set_status(str(user.id), UserStatus.disabled)
    token = await links.issue(str(user.id), "register")

    consume = await service.consume_link(token)
    assert consume.ok is False
    assert consume.reason == "expired"


async def test_create_staff_sends_link_and_creates_invited_staff():
    service, users, _sessions, _links, _lim, email, bg = _make_service()
    staff = await service.create_staff(
        "tutor1", "tutor1@rsu.edu.lv", "Tutor One", UserRole.staff
    )
    assert staff.role == UserRole.staff
    assert staff.status == UserStatus.invited
    await bg.drain()
    assert email.sent[-1][0] == "tutor1@rsu.edu.lv"


async def test_consume_link_rate_limited_per_ip():
    service, _users, _sessions, _links, _lim, _email, _bg = _make_service()
    settings = _settings()
    limit = settings.RATE_LIMIT_CONSUME_PER_IP

    for _ in range(limit):
        result = await service.consume_link("not-a-real-token", "9.9.9.9")
        assert result.reason == "expired"

    blocked = await service.consume_link("not-a-real-token", "9.9.9.9")
    assert blocked.ok is False
    assert blocked.reason == "rate_limited"

    other_ip = await service.consume_link("not-a-real-token", "8.8.8.8")
    assert other_ip.reason == "expired"
