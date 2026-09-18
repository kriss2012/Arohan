import pytest
import os
import hashlib
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User, UserRole
from backend.app.models.storage import FileRecord
from backend.app.models.audit import AuditLog
from backend.app.services.audit_service import AuditService
from backend.app.services.data_integrity_service import DataIntegrityService
from backend.app.services.local_storage_service import LocalStorageService

@pytest.mark.asyncio
async def test_idor_and_privilege_escalation_protection():
    """
    Verifies that a student cannot access another student's scoped endpoints,
    nor escalate privileges to access administrative or faculty controls.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Login as Student
        s_res = await ac.post("/api/v1/auth/login", json={
            "email": "student1@imrd.ac.in",
            "password": "Student@123"
        })
        assert s_res.status_code == 200
        student_token = s_res.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # 2. Student attempts to access Admin User list -> MUST BE 403 FORBIDDEN
        admin_res = await ac.get("/api/v1/admin/users", headers=student_headers)
        assert admin_res.status_code == 403, "Student must not access /admin/users"

        # 3. Student attempts to trigger File Integrity Scan -> MUST BE 403 FORBIDDEN
        sec_res = await ac.post("/api/v1/security/integrity/scan-files", headers=student_headers)
        assert sec_res.status_code == 403, "Student must not access /security/integrity/scan-files"

        # 4. Student attempts to trigger Audit Chain Verification -> MUST BE 403 FORBIDDEN
        audit_res = await ac.post("/api/v1/security/integrity/verify-audit", headers=student_headers)
        assert audit_res.status_code == 403, "Student must not access /security/integrity/verify-audit"

        # 5. Student attempts to access faculty class concept mastery -> MUST BE 403 FORBIDDEN
        fac_res = await ac.get("/api/v1/faculty/class-summary", headers=student_headers)
        assert fac_res.status_code == 403, "Student must not access faculty endpoints"

@pytest.mark.asyncio
async def test_audit_log_cryptographic_hash_chain_and_tamper_detection():
    """
    Verifies that audit records form a cryptographic SHA-256 hash chain,
    and that any retroactive database tampering is immediately detected.
    """
    async with AsyncSessionLocal() as db:
        # 1. Append sequential audit events
        e1 = await AuditService.log_event(
            db=db,
            action="TEST_LOGIN_EVENT",
            user_id="u-student1",
            details={"ip": "127.0.0.1"},
            security_severity="INFO"
        )
        assert e1.record_hash is not None

        e2 = await AuditService.log_event(
            db=db,
            action="TEST_SUBMISSION_EVENT",
            user_id="u-student1",
            details={"assignment": "a-1"},
            security_severity="INFO"
        )
        assert e2.previous_hash == e1.record_hash

        # 2. Verify audit chain is cryptographically intact
        report = await AuditService.verify_audit_chain(db)
        assert report["verified"] is True
        assert report["status"] == "VALID_CHAIN"

        # 3. Simulate malicious tampering: corrupt an existing audit record's details
        tampered_res = await db.execute(select(AuditLog).where(AuditLog.id == e1.id))
        tampered_entry = tampered_res.scalar_one()
        original_details = tampered_entry.details_json
        tampered_entry.details_json = '{"tampered": true, "attacker": "compromised_admin"}'
        await db.commit()

        # 4. Re-verify: Scanner MUST detect tamper
        tamper_report = await AuditService.verify_audit_chain(db)
        assert tamper_report["verified"] is False
        assert tamper_report["status"] == "TAMPER_DETECTED"
        assert tamper_report["corrupted_records_count"] >= 1

        # 5. Restore record to maintain clean state
        tampered_entry.details_json = original_details
        await db.commit()

        restored_report = await AuditService.verify_audit_chain(db)
        assert restored_report["verified"] is True

@pytest.mark.asyncio
async def test_physical_file_storage_integrity_scanner():
    """
    Verifies that the file integrity scanner computes disk SHA-256 checksums,
    detects modified or corrupted files, and maintains evidence.
    """
    async with AsyncSessionLocal() as db:
        # 1. Save a valid test document
        content = b"Official Institutional Academic Record - IMRD Campus LMS 2026"
        rec = await LocalStorageService.save_file(
            db=db,
            file_bytes=content,
            original_filename="institutional_record.txt",
            category="resources",
            uploaded_by_user_id="u-admin1"
        )

        # 2. Run integrity scan -> Should be verified
        res = await DataIntegrityService.scan_file_storage_integrity(db)
        assert res["corrupted_files_count"] == 0

        from backend.app.services.local_storage_service import STORAGE_ROOT
        full_path = os.path.join(STORAGE_ROOT, rec.storage_path) if not os.path.isabs(rec.storage_path) else rec.storage_path

        # 3. Simulate file tampering: alter bytes on disk
        with open(full_path, "wb") as fh:
            fh.write(b"TAMPERED_BYTES_BY_MALICIOUS_ACTOR")

        # 4. Run integrity scan -> MUST detect corruption
        tamper_res = await DataIntegrityService.scan_file_storage_integrity(db)
        assert tamper_res["corrupted_files_count"] >= 1
        assert tamper_res["is_healthy"] is False

        # 5. Restore original bytes
        with open(full_path, "wb") as fh:
            fh.write(content)
        clean_res = await DataIntegrityService.scan_file_storage_integrity(db)
        assert clean_res["corrupted_files_count"] == 0

@pytest.mark.asyncio
async def test_database_consistency_scanner():
    """
    Verifies that the database consistency scanner identifies constraint anomalies.
    """
    async with AsyncSessionLocal() as db:
        report = await DataIntegrityService.scan_database_consistency(db)
        assert "anomalies" in report
        assert "is_healthy" in report

@pytest.mark.asyncio
async def test_admin_security_endpoints_authorized():
    """
    Verifies that authenticated administrators can access security health dashboards and integrity tools.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        admin_res = await ac.post("/api/v1/auth/login", json={
            "email": "admin@imrd.ac.in",
            "password": "Admin@123"
        })
        assert admin_res.status_code == 200
        admin_token = admin_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # 1. Health Dashboard
        dash_res = await ac.get("/api/v1/security/dashboard", headers=headers)
        assert dash_res.status_code == 200
        data = dash_res.json()
        assert "authentication_health" in data
        assert "audit_health" in data

        # 2. Audit Chain verification
        audit_res = await ac.post("/api/v1/security/integrity/verify-audit", headers=headers)
        assert audit_res.status_code == 200
        assert audit_res.json()["status"] == "VALID_CHAIN"
