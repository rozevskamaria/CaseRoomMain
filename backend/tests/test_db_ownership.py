from __future__ import annotations

import itertools

import pytest

from app.db.seed import seed
from app.models.user import UserRole, UserStatus
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.case_repo import CaseRepository
from app.repositories.user_repo import UserRepository
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource

pytestmark = pytest.mark.dbintegration


class FakeLLMClient:
    async def generate(self, system, messages, max_tokens):
        return "x"

    async def generate_structured(self, system, messages, schema, max_tokens):
        return {}

    async def stream(self, system, messages, max_tokens):
        yield "x"


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


async def test_db_attempt_owner_roundtrip(db_session):
    await seed(db_session)
    await db_session.flush()

    users = UserRepository(db_session)
    user = await users.create_student("424299", "Owner")
    await users.set_status(user.id, UserStatus.active)

    service = SessionService(
        FakeLLMClient(),
        store=DbAttemptStore(
            AttemptRepository(db_session), CaseRepository(db_session)
        ),
        cases=DbCaseSource(CaseRepository(db_session)),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )

    proj = await service.start_case("xla", "practice", student_id=str(user.id))
    owner = await service.get_attempt_owner(proj.id)
    assert str(owner) == str(user.id)


async def test_db_attempt_owner_none_when_anonymous(db_session):
    await seed(db_session)
    await db_session.flush()

    service = SessionService(
        FakeLLMClient(),
        store=DbAttemptStore(
            AttemptRepository(db_session), CaseRepository(db_session)
        ),
        cases=DbCaseSource(CaseRepository(db_session)),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )

    proj = await service.start_case("xla", "practice")
    owner = await service.get_attempt_owner(proj.id)
    assert owner is None


async def test_db_user_decrypt_roundtrip(db_session):
    users = UserRepository(db_session)
    user = await users.create_staff(
        "tutor42", "tutor42@rsu.edu.lv", "Tutor FortyTwo", UserRole.staff
    )
    assert await users.decrypt_login_name(user) == "tutor42"
    assert await users.decrypt_email(user) == "tutor42@rsu.edu.lv"
    assert await users.decrypt_full_name(user) == "Tutor FortyTwo"
