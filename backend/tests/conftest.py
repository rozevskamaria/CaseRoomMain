from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.auth import runtime as auth_runtime
from app.core.config import get_settings
from app.main import app
from app.models.user import UserRole, UserStatus

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+asyncpg://caseroom:caseroom@localhost:5433/caseroom"
)


@pytest.fixture(autouse=True)
def _test_crypto_secrets(monkeypatch):
    monkeypatch.setenv("PGCRYPTO_KEY", "test-pgcrypto-key-for-suite")
    monkeypatch.setenv("LOGIN_HASH_PEPPER", "test-login-hash-pepper-for-suite")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _fresh_auth_backend():
    auth_runtime.configure_inmemory()
    yield
    auth_runtime.configure_inmemory()


@pytest_asyncio.fixture
async def student_principal():
    store = auth_runtime.get_user_store(None)
    user = await store.create_student("100100", "Owner Student")
    await store.set_status(str(user.id), UserStatus.active)
    sid = await auth_runtime.get_session_store().create(str(user.id))
    return {"user": user, "user_id": str(user.id), "sid": sid}


@pytest_asyncio.fixture
async def other_student():
    store = auth_runtime.get_user_store(None)
    user = await store.create_student("200200", "Other Student")
    await store.set_status(str(user.id), UserStatus.active)
    sid = await auth_runtime.get_session_store().create(str(user.id))
    return {"user": user, "user_id": str(user.id), "sid": sid}


@pytest_asyncio.fixture
async def disabled_student():
    store = auth_runtime.get_user_store(None)
    user = await store.create_student("300300", "Disabled Student")
    sid = await auth_runtime.get_session_store().create(str(user.id))
    await store.set_status(str(user.id), UserStatus.disabled)
    return {"user": user, "user_id": str(user.id), "sid": sid}


@pytest_asyncio.fixture
async def admin_principal():
    store = auth_runtime.get_user_store(None)
    user = await store.create_staff(
        "admin1", "admin1@rsu.edu.lv", "Admin One", UserRole.admin
    )
    await store.set_status(str(user.id), UserStatus.active)
    sid = await auth_runtime.get_session_store().create(str(user.id))
    return {"user": user, "user_id": str(user.id), "sid": sid}


@pytest_asyncio.fixture
async def staff_principal():
    store = auth_runtime.get_user_store(None)
    user = await store.create_staff(
        "tutor1", "tutor1@rsu.edu.lv", "Tutor One", UserRole.staff
    )
    await store.set_status(str(user.id), UserStatus.active)
    sid = await auth_runtime.get_session_store().create(str(user.id))
    return {"user": user, "user_id": str(user.id), "sid": sid}


def auth_cookies(principal) -> dict[str, str]:
    return {get_settings().SESSION_COOKIE_NAME: principal["sid"]}


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _test_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


@pytest_asyncio.fixture
async def db_engine():
    from sqlalchemy.ext.asyncio import create_async_engine

    from app.models import Base

    engine = create_async_engine(_test_database_url(), future=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as exc:
        await engine.dispose()
        pytest.skip(f"Postgres not reachable at {_test_database_url()}: {exc}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    from sqlalchemy.ext.asyncio import AsyncSession

    async with db_engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
