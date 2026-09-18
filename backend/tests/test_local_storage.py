import pytest
import io
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_file_storage_and_security():
    """Verify local file storage, magic byte blocking of executables, and download with checksum"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login as Faculty
        fac_login = await ac.post("/api/v1/auth/login", json={
            "email": "faculty1@imrd.ac.in",
            "password": "Faculty@123"
        })
        assert fac_login.status_code == 200
        fac_token = fac_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {fac_token}"}

        # 2. Attempt uploading a disguised executable (MZ header in .pdf)
        fake_exe_content = b"MZ\x90\x00\x03\x00\x00\x00SomeExecutablePayload"
        files = {"file": ("malicious.pdf", io.BytesIO(fake_exe_content), "application/pdf")}
        data = {
            "title": "Malicious Assignment",
            "subject_id": "sub-dsa-301",
            "semester_id": "sem-bca-3",
            "division_id": "div-bca-3a",
            "total_marks": 50,
            "passing_marks": 20
        }
        res_blocked = await ac.post("/api/v1/assignments/", headers=headers, data=data, files=files)
        assert res_blocked.status_code == 400
        assert "executable" in res_blocked.json()["detail"].lower()

        # 3. Upload a legitimate PDF assignment
        legit_pdf_content = b"%PDF-1.4\n%Report content for Data Structures Assignment\n%%EOF"
        files_valid = {"file": ("dsa_assignment.pdf", io.BytesIO(legit_pdf_content), "application/pdf")}
        data_valid = {
            "title": "Data Structures Assignment 1",
            "description": "Implement Binary Search Tree",
            "subject_id": "sub-dsa-301",
            "semester_id": "sem-bca-3",
            "division_id": "div-bca-3a",
            "total_marks": 100,
            "passing_marks": 40
        }
        res_created = await ac.post("/api/v1/assignments/", headers=headers, data=data_valid, files=files_valid)
        assert res_created.status_code == 200
        assign_data = res_created.json()
        assert assign_data["title"] == "Data Structures Assignment 1"
        file_id = assign_data["file_id"]
        assert file_id is not None

        # 4. Download file and verify checksum header
        download_res = await ac.get(f"/api/v1/files/{file_id}", headers=headers)
        assert download_res.status_code == 200
        assert download_res.content == legit_pdf_content
        assert "X-Checksum-SHA256" in download_res.headers
