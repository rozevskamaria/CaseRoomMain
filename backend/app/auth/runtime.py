from __future__ import annotations

from collections.abc import Callable
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.email import get_email_service
from app.auth.service import AuthService, Background
from app.auth.stores import (
    InMemoryMagicLinkStore,
    InMemoryRateLimiter,
    InMemorySessionStore,
    InMemoryUserStore,
    MagicLinkStore,
    RateLimiter,
    SessionStore,
    UserStore,
)
from app.core.config import get_settings
from app.models.user import User

_sessions: SessionStore | None = None
_links: MagicLinkStore | None = None
_limiter: RateLimiter | None = None
_user_store_factory: Callable[[AsyncSession | None], UserStore] | None = None

_request_user: ContextVar[User | None] = ContextVar("request_user", default=None)


def _shared_inmemory_factory() -> Callable[[AsyncSession | None], UserStore]:
    store = InMemoryUserStore()

    def factory(session: AsyncSession | None) -> UserStore:
        return store

    return factory


def _ensure_inmemory_defaults() -> None:
    global _sessions, _links, _limiter, _user_store_factory
    if _sessions is None:
        _sessions = InMemorySessionStore(get_settings().SESSION_TTL_SECONDS)
    if _links is None:
        _links = InMemoryMagicLinkStore(get_settings().MAGIC_LINK_TTL_SECONDS)
    if _limiter is None:
        _limiter = InMemoryRateLimiter()
    if _user_store_factory is None:
        _user_store_factory = _shared_inmemory_factory()


def configure_inmemory() -> None:
    global _sessions, _links, _limiter, _user_store_factory
    settings = get_settings()
    _sessions = InMemorySessionStore(settings.SESSION_TTL_SECONDS)
    _links = InMemoryMagicLinkStore(settings.MAGIC_LINK_TTL_SECONDS)
    _limiter = InMemoryRateLimiter()
    _user_store_factory = _shared_inmemory_factory()


def configure_production() -> None:
    global _sessions, _links, _limiter, _user_store_factory
    from app.auth.stores import (
        RedisMagicLinkStore,
        RedisRateLimiter,
        RedisSessionStore,
    )
    from app.core.redis import get_redis
    from app.repositories.user_repo import DbUserStore, UserRepository

    settings = get_settings()
    redis = get_redis()

    def factory(session: AsyncSession | None) -> UserStore:
        return DbUserStore(UserRepository(session))

    _sessions = RedisSessionStore(redis, settings.SESSION_TTL_SECONDS)
    _links = RedisMagicLinkStore(redis, settings.MAGIC_LINK_TTL_SECONDS)
    _limiter = RedisRateLimiter(redis)
    _user_store_factory = factory


def reset() -> None:
    global _sessions, _links, _limiter, _user_store_factory
    _sessions = None
    _links = None
    _limiter = None
    _user_store_factory = None


def get_session_store() -> SessionStore:
    _ensure_inmemory_defaults()
    assert _sessions is not None
    return _sessions


def get_user_store(session: AsyncSession | None) -> UserStore:
    _ensure_inmemory_defaults()
    assert _user_store_factory is not None
    return _user_store_factory(session)


def build_auth_service(
    session: AsyncSession | None, background: Background | None = None
) -> AuthService:
    from app.services.jobs import JobQueue
    from app.workers.queue import get_job_queue

    _ensure_inmemory_defaults()
    assert _sessions is not None and _links is not None and _limiter is not None
    queue: JobQueue | None = None
    if get_settings().APP_ENV == "production":
        queue = get_job_queue()
    return AuthService(
        users=get_user_store(session),
        sessions=_sessions,
        links=_links,
        limiter=_limiter,
        email=get_email_service(),
        settings=get_settings(),
        background=background,
        queue=queue,
    )


async def resolve_current_user(
    sid: str | None, session: AsyncSession | None
) -> User | None:
    if not sid:
        return None
    user_id = await get_session_store().resolve(sid)
    if user_id is None:
        return None
    return await get_user_store(session).get(user_id)


async def dev_login(session: AsyncSession | None, login_name: str) -> str:
    from app.models.user import UserStatus

    users = get_user_store(session)
    user = await users.get_by_login_hash(login_name)
    if user is None:
        user = await users.create_student(login_name, "Dev Student")
    if user.status != UserStatus.active:
        await users.set_status(str(user.id), UserStatus.active)
    return await get_session_store().create(str(user.id))


def set_request_user(user: User | None):
    return _request_user.set(user)


def reset_request_user(token) -> None:
    _request_user.reset(token)


def get_request_user() -> User | None:
    return _request_user.get()
