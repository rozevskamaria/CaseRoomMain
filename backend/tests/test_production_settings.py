from __future__ import annotations

import pytest

from app.core.config import Settings, validate_production_settings


def _prod_settings(**overrides) -> Settings:
    values = {
        "APP_ENV": "production",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "PGCRYPTO_KEY": "pgcrypto-secret",
        "LOGIN_HASH_PEPPER": "pepper-secret",
        "RESEND_API_KEY": "re_test",
        "PUBLIC_BASE_URL": "https://caseroom.tech",
    }
    values.update(overrides)
    return Settings(**values)


def test_development_settings_pass_without_secrets():
    validate_production_settings(Settings(APP_ENV="development"))


def test_complete_production_settings_pass():
    validate_production_settings(_prod_settings())


@pytest.mark.parametrize(
    "missing",
    ["ANTHROPIC_API_KEY", "PGCRYPTO_KEY", "LOGIN_HASH_PEPPER", "RESEND_API_KEY"],
)
def test_production_requires_each_secret(missing):
    with pytest.raises(RuntimeError, match=missing):
        validate_production_settings(_prod_settings(**{missing: ""}))


def test_production_rejects_localhost_public_base_url():
    with pytest.raises(RuntimeError, match="PUBLIC_BASE_URL"):
        validate_production_settings(
            _prod_settings(PUBLIC_BASE_URL="http://localhost:5173")
        )


def test_production_mcp_requires_token_and_pepper():
    with pytest.raises(RuntimeError, match="MCP_ENABLED"):
        validate_production_settings(_prod_settings(MCP_ENABLED=True))
    validate_production_settings(
        _prod_settings(
            MCP_ENABLED=True,
            MCP_RESEARCH_TOKEN="research-token",
            RESEARCH_PSEUDONYM_PEPPER="research-pepper",
        )
    )
