from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.models.user import User, UserSession
from backend.app.models.storage import FileRecord
from backend.app.models.audit import AuditLog
from backend.app.api.deps import require_roles, get_current_user
from backend.app.services.data_integrity_service import DataIntegrityService
from backend.app.services.audit_service import AuditService
from backend.app.services.academic_calculation_service import AcademicCalculationService

router = APIRouter(prefix="/security", tags=["Security & Data Integrity"])

@router.get("/dashboard")
async def get_security_health_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    """
    Returns unified security health metrics for administrative consoles.
    """
    # 1. User & Account Lockout Metrics
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    locked_users = (await db.execute(select(func.count(User.id)).where(User.locked_until != None))).scalar() or 0
    inactive_users = (await db.execute(select(func.count(User.id)).where(User.is_active == False))).scalar() or 0
    active_sessions = (await db.execute(select(func.count(UserSession.id)).where(UserSession.is_revoked == False))).scalar() or 0

    # 2. Audit Trail & Critical Events
    total_audit_events = (await db.execute(select(func.count(AuditLog.id)))).scalar() or 0
    critical_alerts = (await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.security_severity.in_(["HIGH", "CRITICAL"]))
    )).scalar() or 0

    # 3. File Storage Stats
    total_files = (await db.execute(select(func.count(FileRecord.id)))).scalar() or 0

    # 4. Fast Audit Chain Check
    audit_check = await AuditService.verify_audit_chain(db)

    return {
        "status": "OPTIMAL" if audit_check["verified"] and critical_alerts == 0 else "ATTENTION_REQUIRED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "authentication_health": {
            "total_users": total_users,
            "locked_users": locked_users,
            "inactive_users": inactive_users,
            "active_sessions": active_sessions
        },
        "audit_health": {
            "total_events": total_audit_events,
            "critical_events": critical_alerts,
            "audit_chain_valid": audit_check["verified"]
        },
        "storage_health": {
            "total_files_tracked": total_files
        }
    }

@router.post("/integrity/scan-files")
async def scan_file_integrity(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    """
    Executes SHA-256 physical disk integrity check against database metadata.
    """
    report = await DataIntegrityService.scan_file_storage_integrity(db)
    return report

@router.post("/integrity/check-database")
async def check_database_consistency(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    """
    Executes relational and constraint consistency check.
    """
    report = await DataIntegrityService.scan_database_consistency(db)
    return report

@router.post("/integrity/verify-audit")
async def verify_audit_hash_chain(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    """
    Verifies cryptographic hash chain of the audit trail.
    """
    report = await AuditService.verify_audit_chain(db)
    return report

@router.post("/integrity/reconcile-progress/{student_id}")
async def reconcile_student_progress_endpoint(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN", "FACULTY"]))
):
    """
    Reconciles stored student progress score against underlying weighted components.
    """
    report = await AcademicCalculationService.reconcile_student_progress(db, student_id)
    return report
