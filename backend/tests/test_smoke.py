from __future__ import annotations

from httpx import ASGITransport, AsyncClient


async def test_app_imports_and_wires_transports() -> None:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        assert (await ac.get("/health")).status_code == 200
        assert (await ac.get("/sse/ping")).status_code == 200
        gql = await ac.post("/graphql", json={"query": "{ ping }"})
        assert gql.status_code == 200


async def test_schema_has_query() -> None:
    from app.api.graphql.schema import schema

    query_type = schema.schema_converter.type_map["Query"]
    assert query_type is not None
    field_names = {f.name for f in query_type.definition.fields}
    assert {"ping", "version", "health"} <= field_names


async def test_settings_load() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.APP_ENV == "development"
    assert settings.ANTHROPIC_MODEL == "claude-sonnet-4-6"
    assert settings.cors_origins_list == ["http://localhost:5173"]
    assert settings.DATABASE_URL.startswith("postgresql+asyncpg://")
