import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.models.user import User, UserRole, UserSession, StudentEnrollment
from backend.app.models.storage import FileRecord
from backend.app.models.assignment import Assignment, AssignmentSubmission
from backend.app.models.progress import Result, StudentProgress
from backend.app.services.audit_service import AuditService
from backend.app.services.academic_calculation_service import AcademicCalculationService

class DataIntegrityService:
    """
    Comprehensive institutional data integrity and consistency scanner.
    """

    @classmethod
    async def scan_file_storage_integrity(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Scans all stored files, recalculates physical SHA-256 checksums, and compares against DB records.
        """
        result = await db.execute(select(FileRecord))
        files = result.scalars().all()

        total_files = len(files)
        verified_files = 0
        missing_files = []
        corrupted_files = []

        for f in files:
            path = f.storage_path
            if not os.path.isabs(path):
                from backend.app.services.local_storage_service import STORAGE_ROOT
                path = os.path.join(STORAGE_ROOT, path)

            if not os.path.exists(path):
                missing_files.append({
                    "file_id": f.id,
                    "expected_path": path,
                    "original_name": f.original_filename
                })
                continue

            # Read bytes and recompute SHA-256
            hasher = hashlib.sha256()
            try:
                with open(path, "rb") as fh:
                    while chunk := fh.read(65536):
                        hasher.update(chunk)
                computed_hash = hasher.hexdigest()

                if computed_hash != f.checksum_sha256:
                    corrupted_files.append({
                        "file_id": f.id,
                        "file_path": path,
                        "expected_hash": f.checksum_sha256,
                        "actual_hash": computed_hash,
                        "original_name": f.original_filename
                    })
                else:
                    verified_files += 1
            except Exception as e:
                corrupted_files.append({
                    "file_id": f.id,
                    "file_path": path,
                    "error": str(e),
                    "original_name": f.original_filename
                })

        is_healthy = len(missing_files) == 0 and len(corrupted_files) == 0

        if not is_healthy:
            await AuditService.log_event(
                db=db,
                action="FILE_INTEGRITY_ALERT",
                details={
                    "total_files": total_files,
                    "missing_count": len(missing_files),
                    "corrupted_count": len(corrupted_files),
                    "missing_files": missing_files,
                    "corrupted_files": corrupted_files
                },
                security_severity="CRITICAL" if len(corrupted_files) > 0 else "HIGH"
            )

        return {
            "total_files": total_files,
            "verified_files": verified_files,
            "missing_files_count": len(missing_files),
            "corrupted_files_count": len(corrupted_files),
            "missing_files": missing_files,
            "corrupted_files": corrupted_files,
            "is_healthy": is_healthy
        }

    @classmethod
    async def scan_database_consistency(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Validates referential integrity, constraints, orphan records, and boundary violations.
        """
        anomalies = []

        # 1. Check for users with no assigned roles
        u_res = await db.execute(
            select(User.id, User.email)
            .outerjoin(UserRole, User.id == UserRole.user_id)
            .where(UserRole.role_name == None)
        )
        orphan_users = u_res.all()
        for u in orphan_users:
            anomalies.append({
                "type": "USER_NO_ROLES",
                "entity": "User",
                "id": u.id,
                "detail": f"User {u.email} has no assigned roles."
            })

        # 2. Check for invalid marks in results (marks > max_marks or marks < 0)
        r_res = await db.execute(
            select(Result)
            .where(
                (Result.marks < 0.0) |
                (Result.marks > Result.max_marks) |
                (Result.percentage < 0.0) |
                (Result.percentage > 100.0)
            )
        )
        invalid_results = r_res.scalars().all()
        for r in invalid_results:
            anomalies.append({
                "type": "INVALID_RESULT_RANGE",
                "entity": "Result",
                "id": r.id,
                "detail": f"Result marks={r.marks}, max_marks={r.max_marks}, percentage={r.percentage}% violate valid boundaries."
            })

        # 3. Check for submissions referencing deleted assignments
        s_res = await db.execute(
            select(AssignmentSubmission.id, AssignmentSubmission.assignment_id)
            .outerjoin(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
            .where(Assignment.id == None)
        )
        orphan_subs = s_res.all()
        for s in orphan_subs:
            anomalies.append({
                "type": "ORPHAN_SUBMISSION",
                "entity": "AssignmentSubmission",
                "id": s.id,
                "detail": f"Submission references non-existent assignment {s.assignment_id}."
            })

        # 4. Check for dangling active sessions with revoked users
        sess_res = await db.execute(
            select(UserSession.id, UserSession.user_id)
            .join(User, UserSession.user_id == User.id)
            .where(
                (User.is_active == False) | (User.status == "INACTIVE"),
                UserSession.is_revoked == False
            )
        )
        dangling_sessions = sess_res.all()
        for sess in dangling_sessions:
            anomalies.append({
                "type": "DANGLING_SESSION_ON_INACTIVE_USER",
                "entity": "UserSession",
                "id": sess.id,
                "detail": f"Active session found on inactive user {sess.user_id}."
            })

        is_healthy = len(anomalies) == 0

        if not is_healthy:
            await AuditService.log_event(
                db=db,
                action="DATABASE_CONSISTENCY_ALERT",
                details={
                    "total_anomalies": len(anomalies),
                    "anomalies": anomalies
                },
                security_severity="HIGH"
            )

        return {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies,
            "is_healthy": is_healthy
        }

    @classmethod
    async def generate_integrity_report(cls, db: AsyncSession) -> Dict[str, Any]:
        """
        Aggregates file integrity, database consistency, and audit chain verification into a single report.
        """
        file_health = await cls.scan_file_storage_integrity(db)
        db_health = await cls.scan_database_consistency(db)
        audit_chain = await AuditService.verify_audit_chain(db)

        overall_status = "OPTIMAL"
        if not file_health["is_healthy"] or not db_health["is_healthy"] or not audit_chain["verified"]:
            overall_status = "ACTION_REQUIRED"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "file_integrity": file_health,
            "database_consistency": db_health,
            "audit_chain_verification": audit_chain
        }
