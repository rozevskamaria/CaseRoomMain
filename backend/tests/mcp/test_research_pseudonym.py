from __future__ import annotations

import hashlib
import hmac
import uuid

import pytest

from app.services.research_pseudonym import (
    ResearchPseudonymError,
    assert_pepper_distinct,
    research_pseudonym,
)

PEPPER = "research-pepper-distinct-value"
OTHER_PEPPER = "a-totally-different-pepper"


def test_pseudonym_deterministic_and_stable():
    uid = uuid.uuid4()
    first = research_pseudonym(uid, PEPPER)
    second = research_pseudonym(uid, PEPPER)
    assert first == second
    assert len(first) == 64
    assert first == research_pseudonym(str(uid), PEPPER)


def test_pseudonym_distinct_across_students():
    a = research_pseudonym(uuid.uuid4(), PEPPER)
    b = research_pseudonym(uuid.uuid4(), PEPPER)
    assert a != b


def test_pseudonym_rotation_changes_every_pseudonym():
    uid = uuid.uuid4()
    assert research_pseudonym(uid, PEPPER) != research_pseudonym(uid, OTHER_PEPPER)


def test_pseudonym_non_reversible_hmac_over_uuid():
    uid = uuid.uuid4()
    pseudo = research_pseudonym(uid, PEPPER)
    assert str(uid) not in pseudo
    assert uid.hex not in pseudo
    expected = hmac.new(
        PEPPER.encode(), str(uid).encode(), hashlib.sha256
    ).hexdigest()
    assert pseudo == expected


def test_pseudonym_differs_from_login_hash_construction():
    uid = uuid.uuid4()
    login_pepper = "login-hash-pepper"
    pseudo = research_pseudonym(uid, PEPPER)
    login_like = hmac.new(
        login_pepper.encode(), str(uid).encode(), hashlib.sha256
    ).hexdigest()
    assert pseudo != login_like


def test_empty_pepper_fails_closed():
    with pytest.raises(ResearchPseudonymError):
        research_pseudonym(uuid.uuid4(), "")


def test_null_student_refused():
    with pytest.raises(ResearchPseudonymError):
        research_pseudonym(None, PEPPER)


def test_assert_distinct_rejects_pgcrypto_collision():
    with pytest.raises(ResearchPseudonymError):
        assert_pepper_distinct("same", "same", "other")


def test_assert_distinct_rejects_login_pepper_collision():
    with pytest.raises(ResearchPseudonymError):
        assert_pepper_distinct("same", "other", "same")


def test_assert_distinct_rejects_empty():
    with pytest.raises(ResearchPseudonymError):
        assert_pepper_distinct("", "x", "y")


def test_assert_distinct_accepts_distinct_pepper():
    assert_pepper_distinct(PEPPER, "pgcrypto", "loginpepper")
