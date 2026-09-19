import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_spa_and_static_serving():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Health check
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

        # 2. Root SPA route
        res = await client.get("/")
        assert res.status_code == 200
        assert "html" in res.headers.get("content-type", "")

        # 3. Client-side SPA navigation route (fallback to index.html)
        res = await client.get("/dashboard")
        assert res.status_code == 200
        assert "html" in res.headers.get("content-type", "")

        # 4. Another client-side SPA navigation route
        res = await client.get("/curriculum/subjects")
        assert res.status_code == 200
        assert "html" in res.headers.get("content-type", "")

        # 5. Static asset route
        res = await client.get("/logo.png")
        assert res.status_code == 200

        # 6. OpenAPI route
        res = await client.get("/api/v1/openapi.json")
        assert res.status_code == 200
