from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.arohan import PlacementReadinessProfile
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/placement", tags=["Placement Readiness"])

@router.get("/readiness/{student_id}")
async def get_placement_readiness(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(PlacementReadinessProfile).where(PlacementReadinessProfile.student_id == student_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        # Fallback profile
        return {
            "student_id": student_id,
            "overall_readiness_index": 0.0,
            "status": "INSUFFICIENT_EVIDENCE",
            "message": "Complete at least one MCAT diagnostic and curriculum module to establish readiness indicators."
        }

    return {
        "student_id": student_id,
        "overall_readiness_index": profile.overall_readiness_index,
        "dimensions": {
            "technical": profile.technical_score,
            "coding": profile.coding_score,
            "aptitude": profile.aptitude_score,
            "projects": profile.project_score,
            "consistency": profile.consistency_score
        },
        "evidence_verified": profile.evidence_verified,
        "last_updated": profile.last_updated.isoformat(),
        "status": "DEVELOPING" if profile.overall_readiness_index < 75 else "READINESS_ESTABLISHED"
    }
