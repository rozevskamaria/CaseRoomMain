from __future__ import annotations

import pytest
from sqlalchemy import bindparam, func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.models.user import User, UserRole, UserStatus
from app.repositories.user_repo import UserRepository

pytestmark = pytest.mark.dbintegration


async def test_create_student_roundtrip(db_session):
    repo = UserRepository(db_session)
    user = await repo.create_student("123456", "Ada Lovelace")

    assert user.role == UserRole.student
    assert isinstance(user.login_name, bytes)
    assert isinstance(user.email, bytes)

    assert await repo.decrypt_login_name(user) == "123456"
    assert await repo.decrypt_email(user) == "123456@rsu.edu.lv"
    assert await repo.decrypt_full_name(user) == "Ada Lovelace"


async def test_create_staff_roundtrip(db_session):
    repo = UserRepository(db_session)
    user = await repo.create_staff(
        "tutor", "tutor@rsu.edu.lv", "Grace Hopper", UserRole.staff
    )

    assert user.role == UserRole.staff
    assert await repo.decrypt_login_name(user) == "tutor"
    assert await repo.decrypt_email(user) == "tutor@rsu.edu.lv"
    assert await repo.decrypt_full_name(user) == "Grace Hopper"


async def test_get_by_login_hash_finds_without_decrypting(db_session):
    repo = UserRepository(db_session)
    created = await repo.create_student("654321", None)

    found = await repo.get_by_login_hash("654321")
    assert found is not None
    assert found.id == created.id

    assert await repo.get_by_login_hash("000000") is None


async def test_login_name_hash_is_hmac_not_bare_sha256(db_session):
    repo = UserRepository(db_session)
    user = await repo.create_student("424242", None)

    settings = get_settings()
    hmac_hash = await db_session.scalar(
        select(
            func.encode(
                func.hmac("424242", bindparam(None, settings.LOGIN_HASH_PEPPER), "sha256"),
                "hex",
            )
        )
    )
    bare_sha256 = await db_session.scalar(
        select(func.encode(func.digest("424242", "sha256"), "hex"))
    )

    assert user.login_name_hash == hmac_hash
    assert user.login_name_hash != bare_sha256


async def test_duplicate_login_name_conflicts(db_session):
    repo = UserRepository(db_session)
    await repo.create_student("303030", None)

    with pytest.raises(IntegrityError):
        await repo.create_student("303030", None)


async def test_set_status_and_stamp_consent(db_session):
    repo = UserRepository(db_session)
    user = await repo.create_student("191919", None)
    assert user.status == UserStatus.invited

    await repo.set_status(user.id, UserStatus.active)
    await repo.stamp_consent(user.id, "v1")

    refreshed = await db_session.get(User, user.id)
    await db_session.refresh(refreshed)
    assert refreshed.status == UserStatus.active
    assert refreshed.consent_version == "v1"
    assert refreshed.consent_at is not None
