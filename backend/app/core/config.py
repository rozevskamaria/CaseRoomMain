from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    APP_ENV: str = "development"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    CASEROOM_ROUTING: str = "hybrid"

    DATABASE_URL: str = "postgresql+asyncpg://caseroom:caseroom@postgres:5432/caseroom"
    PGCRYPTO_KEY: str = ""
    LOGIN_HASH_PEPPER: str = ""
    REDIS_URL: str = "redis://redis:6379/0"

    CORS_ORIGINS: str = "http://localhost:5173"

    SESSION_COOKIE_NAME: str = "caseroom_session"
    SESSION_TTL_SECONDS: int = 1209600
    MAGIC_LINK_TTL_SECONDS: int = 900
    CONSENT_VERSION: str = "v1"

    PUBLIC_BASE_URL: str = "http://localhost:5173"
    RESEND_API_KEY: str = ""
    RESEND_SENDER: str = "CaseRoom <noreply@caseroom.tech>"

    CASEROOM_ADMIN_LOGIN: str = ""
    CASEROOM_ADMIN_EMAIL: str = ""

    RATE_LIMIT_REQUEST_LINK_PER_SUBJECT: int = 5
    RATE_LIMIT_REQUEST_LINK_PER_IP: int = 20
    RATE_LIMIT_REQUEST_LINK_WINDOW_SECONDS: int = 600
    RATE_LIMIT_REGISTER_PER_SUBJECT: int = 5
    RATE_LIMIT_REGISTER_PER_IP: int = 3
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 3600
    RATE_LIMIT_CONSUME_PER_IP: int = 30
    RATE_LIMIT_CONSUME_WINDOW_SECONDS: int = 600

    MCP_ENABLED: bool = False
    MCP_RESEARCH_TOKEN: str = ""
    RESEARCH_PSEUDONYM_PEPPER: str = ""
    K_ANON_THRESHOLD: int = 5

    RESEARCH_EXPORT_DIR: str = "/tmp/caseroom-exports"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def admin_logins_list(self) -> list[str]:
        return [
            login.strip()
            for login in self.CASEROOM_ADMIN_LOGIN.split(",")
            if login.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
