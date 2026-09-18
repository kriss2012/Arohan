from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.progress import StudentProgress, Result, SkillEvidence
from backend.app.services.progress_service import ProgressService
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/progress", tags=["Student Progress Engine"])

@router.get("/my-progress")
async def get_my_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_student_progress(student_id=current_user.id, db=db, current_user=current_user)

@router.get("/student/{student_id}")
@router.get("/{student_id}")
async def get_student_progress(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # IDOR Check: Students can only access their own progress
    from backend.app.models.user import UserRole
    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == current_user.id))
    user_roles = roles_res.scalars().all()
    if "STUDENT" in user_roles and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access forbidden: cannot view other students' progress.")

    progress = await ProgressService.recalculate_student_progress(db, student_id)

    # Fetch recent published results
    res_query = await db.execute(
        select(Result).where(Result.student_id == student_id, Result.published == True).order_by(Result.published_at.desc())
    )
    results = res_query.scalars().all()

    # Fetch recent skill evidence
    ev_query = await db.execute(
        select(SkillEvidence).where(SkillEvidence.student_id == student_id).order_by(SkillEvidence.recorded_at.desc()).limit(10)
    )
    evidence_list = ev_query.scalars().all()

    return {
        "student_id": student_id,
        "overall_progress": progress.overall_progress,
        "completion_percentage": progress.completion_percentage,
        "assignment_score": progress.assignment_score,
        "assessment_score": progress.assessment_score,
        "mcat_score": progress.mcat_score,
        "coding_score": progress.coding_score,
        "project_score": progress.project_score,
        "activity_score": progress.activity_score,
        "consistency_score": progress.consistency_score,
        "last_activity_at": progress.last_activity_at.isoformat() if progress.last_activity_at else None,
        "recent_results": [
            {
                "id": r.id,
                "subject_id": r.subject_id,
                "marks": r.marks,
                "max_marks": r.max_marks,
                "percentage": r.percentage,
                "grade": r.grade,
                "status": r.result_status,
                "published_at": r.published_at.isoformat()
            }
            for r in results
        ],
        "recent_evidence": [
            {
                "id": e.id,
                "skill_id": e.skill_id,
                "source_type": e.source_type,
                "score": e.score,
                "normalized_score": e.normalized_score,
                "confidence": e.confidence,
                "recorded_at": e.recorded_at.isoformat()
            }
            for e in evidence_list
        ]
    }
