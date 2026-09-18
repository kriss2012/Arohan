import csv
import io
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from backend.app.core.database import get_db
from backend.app.models.user import User, AuthorizedUser, StudentProfile, FacultyProfile, UserRole
from backend.app.models.assignment import Assignment, AssignmentSubmission
from backend.app.schemas.admin import (
    AuthorizedUserCreate, AuthorizedUserOut, BulkImportValidationReport,
    UserStatusUpdate, DatabaseHealthOut, StorageStatsOut, BackupOut
)
from backend.app.schemas.auth import UserSummary
from backend.app.services.backup_service import BackupService
from backend.app.services.email_service import EmailService
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import require_roles
from backend.app.core.config import settings

router = APIRouter(prefix="/admin", tags=["Institute Administration"])

@router.post("/authorized-users", response_model=AuthorizedUserOut)
async def add_authorized_user(
    payload: AuthorizedUserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    # Check if email already authorized
    existing = await db.execute(select(AuthorizedUser).where(AuthorizedUser.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="This email is already in the authorized allowlist.")

    auth_user = AuthorizedUser(
        email=payload.email,
        full_name=payload.full_name,
        intended_role=payload.intended_role,
        department_id=payload.department_id,
        program_id=payload.program_id,
        academic_year_id=payload.academic_year_id,
        division_id=payload.division_id,
        student_or_emp_id=payload.student_or_emp_id,
        activation_code=f"ACT-{uuid.uuid4().hex[:8].upper()}",
        status="INVITED",
        invited_by=current_user.id
    )
    db.add(auth_user)
    await db.commit()
    await db.refresh(auth_user)

    # Send professional account authorization invitation email
    EmailService.send_invitation_email(
        to_email=payload.email,
        full_name=payload.full_name,
        role_name=payload.intended_role
    )

    return auth_user

@router.get("/authorized-users", response_model=List[AuthorizedUserOut])
async def list_authorized_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    result = await db.execute(select(AuthorizedUser).order_by(AuthorizedUser.created_at.desc()))
    return result.scalars().all()

@router.post("/authorized-users/bulk-import", response_model=BulkImportValidationReport)
async def bulk_import_authorized_users(
    file: UploadFile = File(...),
    commit: bool = Query(False, description="Set to true to persist valid rows after review"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    content = await file.read()
    text = content.decode("utf-8-sig", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    seen_emails = set()
    valid_rows = []
    invalid_rows = []
    duplicate_emails = []
    already_authorized = []

    for idx, row in enumerate(reader, 1):
        email = (row.get("email") or "").strip().lower()
        full_name = (row.get("full_name") or row.get("name") or "").strip()
        role = (row.get("role") or row.get("intended_role") or "STUDENT").strip().upper()
        eid = (row.get("student_id") or row.get("employee_id") or "").strip()

        if not email or "@" not in email:
            invalid_rows.append({"row": idx, "reason": "Invalid email address format."})
            continue

        if email in seen_emails:
            duplicate_emails.append(email)
            invalid_rows.append({"row": idx, "reason": f"Duplicate email in CSV: {email}"})
            continue
        seen_emails.add(email)

        # Check DB
        res = await db.execute(select(AuthorizedUser).where(AuthorizedUser.email == email))
        if res.scalar_one_or_none():
            already_authorized.append(email)
            invalid_rows.append({"row": idx, "reason": f"Email already authorized in database: {email}"})
            continue

        valid_rows.append({
            "email": email,
            "full_name": full_name or "New Member",
            "intended_role": role,
            "student_or_emp_id": eid
        })

    # Commit if requested
    if commit and valid_rows:
        for r in valid_rows:
            db.add(AuthorizedUser(
                email=r["email"],
                full_name=r["full_name"],
                intended_role=r["intended_role"],
                student_or_emp_id=r["student_or_emp_id"],
                activation_code=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                status="INVITED",
                invited_by=current_user.id
            ))
        await db.commit()

    return BulkImportValidationReport(
        total_rows=len(valid_rows) + len(invalid_rows),
        valid_rows_count=len(valid_rows),
        invalid_rows_count=len(invalid_rows),
        duplicates_in_csv=duplicate_emails,
        already_authorized_emails=already_authorized,
        errors=invalid_rows
    )

@router.get("/users")
async def list_users(
    role: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    query = select(User)
    if status_filter:
        query = query.where(User.status == status_filter)
    result = await db.execute(query)
    users = result.scalars().all()

    out = []
    for u in users:
        roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == u.id))
        user_roles = list(roles_res.scalars().all())
        if role and role not in user_roles:
            continue
        out.append({
            "id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "status": u.status,
            "roles": user_roles,
            "is_authorized": getattr(u, "is_authorized", True),
            "is_active": getattr(u, "is_active", True),
            "is_email_verified": getattr(u, "is_email_verified", False),
            "has_password": bool(u.password_hash),
            "failed_login_attempts": u.failed_login_attempts,
            "locked_until": u.locked_until.isoformat() if u.locked_until else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        })
    return out

@router.post("/users/{user_id}/unlock")
async def unlock_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.failed_login_attempts = 0
    user.locked_until = None
    user.status = "ACTIVE"
    await db.commit()
    return {"message": f"User {user.email} successfully unlocked."}

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    user.status = "INACTIVE"
    # Immediately revoke all active sessions
    await AuthService.revoke_all_user_sessions(db, user.id)
    await db.commit()
    return {"message": f"User {user.email} has been deactivated and all active sessions revoked."}

@router.post("/users/{user_id}/reactivate")
async def reactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    user.status = "ACTIVE"
    user.failed_login_attempts = 0
    user.locked_until = None
    await db.commit()
    return {"message": f"User {user.email} has been reactivated."}

@router.post("/users/{user_id}/revoke-sessions")
async def admin_revoke_sessions(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    await AuthService.revoke_all_user_sessions(db, user_id)
    return {"message": f"All active sessions for user {user_id} have been revoked."}

@router.post("/users/{user_id}/resend-invitation")
async def resend_user_invitation(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == user.id))
    roles = roles_res.scalars().all()
    primary_role = roles[0] if roles else "STUDENT"

    EmailService.send_invitation_email(
        to_email=user.email,
        full_name=f"{user.first_name} {user.last_name}",
        role_name=primary_role
    )
    return {"message": f"Invitation email resent to {user.email}."}

@router.get("/database/health", response_model=DatabaseHealthOut)
async def get_database_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    u_count = (await db.execute(select(func.count(User.id)))).scalar() or 0
    s_count = (await db.execute(select(func.count(StudentProfile.user_id)))).scalar() or 0
    f_count = (await db.execute(select(func.count(FacultyProfile.user_id)))).scalar() or 0
    a_count = (await db.execute(select(func.count(Assignment.id)))).scalar() or 0
    sub_count = (await db.execute(select(func.count(AssignmentSubmission.id)))).scalar() or 0

    return DatabaseHealthOut(
        database_connected=True,
        database_engine=settings.DATABASE_URL.split("://")[0],
        active_connections=1,
        total_users=u_count,
        total_students=s_count,
        total_faculty=f_count,
        total_assignments=a_count,
        total_submissions=sub_count,
        system_status="OPTIMAL"
    )

@router.get("/storage/stats", response_model=StorageStatsOut)
async def get_storage_stats(
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    stats = BackupService.get_storage_statistics()
    return StorageStatsOut(
        storage_root=stats["storage_root"],
        total_bytes=stats["total_bytes"],
        category_breakdown=stats["category_breakdown"]
    )

@router.post("/backups/create", response_model=BackupOut)
async def create_backup(
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    report = BackupService.create_backup()
    return BackupOut(**report)

@router.get("/backups", response_model=List[BackupOut])
async def list_backups(
    current_user: User = Depends(require_roles(["SUPER_ADMIN", "INSTITUTE_ADMIN"]))
):
    backups = BackupService.list_backups()
    return [BackupOut(**b) for b in backups]

@router.post("/backups/{filename}/restore")
async def restore_backup(
    filename: str,
    current_user: User = Depends(require_roles(["SUPER_ADMIN"]))
):
    result = BackupService.verify_and_restore_backup(filename)
    return result
