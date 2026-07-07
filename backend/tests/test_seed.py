from __future__ import annotations

import itertools

import pytest
from sqlalchemy import func, select

from app.content.cases import CASES
from app.db.seed import seed
from app.models.case import (
    Case as CaseModel,
    CaseLocalization,
    CaseTest,
    CaseVersion,
)
from app.repositories.attempt_repo import AttemptRepository
from app.repositories.case_repo import CaseRepository
from app.services.session import SessionService
from app.services.stores import DbAttemptStore, DbCaseSource, RegistryCaseSource

pytestmark = pytest.mark.dbintegration


class FakeLLMClient:
    async def generate(self, system, messages, max_tokens):
        return "noop"

    async def stream(self, system, messages, max_tokens):
        if False:
            yield ""


def _ids():
    counter = itertools.count(1)
    return lambda: f"id-{next(counter)}"


async def _count(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model))


async def test_seed_parity(db_session):
    await seed(db_session)
    await db_session.flush()

    source = DbCaseSource(CaseRepository(db_session))
    for slug, registry_case in CASES.items():
        db_case = await source.get_case(slug, "en")
        assert db_case == registry_case
        assert list(db_case.lab_data.keys()) == list(registry_case.lab_data.keys())


async def test_seed_idempotent(db_session):
    await seed(db_session)
    await db_session.flush()

    counts_first = {
        "cases": await _count(db_session, CaseModel),
        "case_versions": await _count(db_session, CaseVersion),
        "case_localizations": await _count(db_session, CaseLocalization),
        "case_tests": await _count(db_session, CaseTest),
    }

    await seed(db_session)
    await db_session.flush()

    counts_second = {
        "cases": await _count(db_session, CaseModel),
        "case_versions": await _count(db_session, CaseVersion),
        "case_localizations": await _count(db_session, CaseLocalization),
        "case_tests": await _count(db_session, CaseTest),
    }

    assert counts_first == counts_second
    assert counts_first["cases"] == len(CASES)
    assert counts_first["case_versions"] == len(CASES)
    assert counts_first["case_localizations"] == len(CASES)
    assert counts_first["case_tests"] == sum(
        len(case.lab_data) for case in CASES.values()
    )


async def test_seed_db_e2e(db_session):
    await seed(db_session)
    await db_session.flush()

    db_service = SessionService(
        FakeLLMClient(),
        store=DbAttemptStore(
            AttemptRepository(db_session), CaseRepository(db_session)
        ),
        cases=DbCaseSource(CaseRepository(db_session)),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )
    mem_service = SessionService(
        FakeLLMClient(),
        cases=RegistryCaseSource(),
        rng=lambda: 0.0,
        id_factory=_ids(),
    )

    db_proj = await db_service.start_case("xla", "practice")
    mem_proj = await mem_service.start_case("xla", "practice")

    db_proj = await db_service.send_test_order(db_proj.id, "immunoglobulins")
    mem_proj = await mem_service.send_test_order(mem_proj.id, "immunoglobulins")

    db_labs = [m for m in db_proj.messages if m.type == "lab"]
    mem_labs = [m for m in mem_proj.messages if m.type == "lab"]

    assert len(db_labs) == 1
    assert [(m.type, m.text) for m in db_labs] == [
        (m.type, m.text) for m in mem_labs
    ]
    assert db_proj.ordered_tests == mem_proj.ordered_tests
    assert db_proj.phase == mem_proj.phase


async def test_lv_localization_falls_back_to_en_verbatim(db_session):
    await seed(db_session)
    repo = CaseRepository(db_session)
    en = await repo.get_published_case("xla", "en")
    lv = await repo.get_published_case("xla", "lv")
    assert lv is not None
    assert lv == en
