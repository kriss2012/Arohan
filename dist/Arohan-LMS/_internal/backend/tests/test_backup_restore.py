import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_backup_and_health_monitoring():
    """Verify admin database health endpoint and local backup creation/listing"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login as Admin
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@imrd.ac.in",
            "password": "Admin@123"
        })
        assert admin_login.status_code == 200
        token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check Database Health
        health_resp = await ac.get("/api/v1/admin/database/health", headers=headers)
        assert health_resp.status_code == 200
        health = health_resp.json()
        assert health["database_connected"] is True
        assert health["system_status"] in ["OPTIMAL", "OPERATIONAL"]

        # 3. Check Storage Stats
        storage_resp = await ac.get("/api/v1/admin/storage/stats", headers=headers)
        assert storage_resp.status_code == 200
        storage = storage_resp.json()
        assert "storage_root" in storage
        assert "total_bytes" in storage

        # 4. Trigger Local Backup
        backup_resp = await ac.post("/api/v1/admin/backups/create", headers=headers)
        assert backup_resp.status_code == 200
        backup_res = backup_resp.json()
        assert "backup_id" in backup_res
        assert "filename" in backup_res
        assert "checksum_sha256" in backup_res

        # 5. List Backups
        list_backups = await ac.get("/api/v1/admin/backups", headers=headers)
        assert list_backups.status_code == 200
        backups = list_backups.json()
        assert len(backups) > 0
        assert any(b["filename"] == backup_res["filename"] for b in backups)
