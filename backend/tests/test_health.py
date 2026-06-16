from __future__ import annotations

from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_graphql_ping_version_health(client: AsyncClient) -> None:
    resp = await client.post("/graphql", json={"query": "{ ping version health }"})
    assert resp.status_code == 200

    payload = resp.json()
    assert "errors" not in payload, payload
    data = payload["data"]
    assert data["ping"] == "pong"
    assert data["health"] == "ok"
    assert data["version"] == "0.1.0"


async def test_sse_ping_stream(client: AsyncClient) -> None:
    resp = await client.get("/sse/ping")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    body = resp.text
    for n in range(3):
        assert f'data: {{"tick": {n}}}' in body
