from __future__ import annotations

import pytest

from app.auth.bootstrap import ensure_admin
from app.core.config import Settings
from app.models.user import UserRole, UserStatus
from app.repositories.user_repo import UserRepository

pytestmark = pytest.mark.dbintegration


def _settings() -> Settings:
    return Settings(
        PGCRYPTO_KEY="test-pgcrypto-key-for-suite",
        LOGIN_HASH_PEPPER="test-login-hash-pepper-for-suite",
        CASEROOM_ADMIN_LOGIN="rootadmin",
        CASEROOM_ADMIN_EMAIL="rootadmin@rsu.edu.lv",
    )


async def test_ensure_admin_creates_active_admin_and_is_idempotent(db_session):
    settings = _settings()
    await ensure_admin(db_session, settings)

    repo = UserRepository(db_session)
    user = await repo.get_by_login_hash("rootadmin")
    assert user is not None
    assert user.role == UserRole.admin
    assert user.status == UserStatus.active

    await ensure_admin(db_session, settings)
    again = await repo.get_by_login_hash("rootadmin")
    assert again.id == user.id


async def test_ensure_admin_noop_without_config(db_session):
    settings = Settings(
        PGCRYPTO_KEY="test-pgcrypto-key-for-suite",
        LOGIN_HASH_PEPPER="test-login-hash-pepper-for-suite",
    )
    await ensure_admin(db_session, settings)
    repo = UserRepository(db_session)
    assert await repo.get_by_login_hash("rootadmin") is None
