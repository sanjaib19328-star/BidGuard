import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        # 200 when PostgreSQL is connected, 503 when DB is offline/initializing
        assert response.status_code in (200, 503)
        data = response.json()
        assert data["service"] == settings.PROJECT_NAME
        assert data["version"] == settings.VERSION
        assert "database" in data
        assert data["database"] in ("connected", "disconnected")


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["health"] == "/api/health"
        assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_openapi_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/health" in data["paths"]
