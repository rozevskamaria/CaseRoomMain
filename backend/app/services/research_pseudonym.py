from __future__ import annotations

import hashlib
import hmac


class ResearchPseudonymError(Exception):
    pass


def assert_pepper_distinct(
    pepper: str, pgcrypto_key: str, login_hash_pepper: str
) -> None:
    if not pepper:
        raise ResearchPseudonymError(
            "RESEARCH_PSEUDONYM_PEPPER is unset; refusing to emit research data"
        )
    if pepper == pgcrypto_key:
        raise ResearchPseudonymError(
            "RESEARCH_PSEUDONYM_PEPPER must differ from PGCRYPTO_KEY"
        )
    if pepper == login_hash_pepper:
        raise ResearchPseudonymError(
            "RESEARCH_PSEUDONYM_PEPPER must differ from LOGIN_HASH_PEPPER"
        )


def research_pseudonym(user_id, pepper: str) -> str:
    if not pepper:
        raise ResearchPseudonymError(
            "RESEARCH_PSEUDONYM_PEPPER is unset; refusing to emit research data"
        )
    if user_id is None:
        raise ResearchPseudonymError("cannot pseudonymize a null student id")
    return hmac.new(
        pepper.encode(), str(user_id).encode(), hashlib.sha256
    ).hexdigest()
