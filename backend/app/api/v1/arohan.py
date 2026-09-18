from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.evidence import Skill, StudentSkillCompetency
from backend.app.schemas.arohan import RecommendationOut, SkillCompetencyOut, EvidenceDrawerOut
from backend.app.services.arohan_service import ArohanService
from backend.app.services.bkt_service import BKTService
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/arohan", tags=["AROHAN AI"])

@router.get("/recommendations", response_model=List[RecommendationOut])
async def get_student_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recs = await ArohanService.get_or_generate_recommendations(
        db=db,
        student_id=current_user.id
    )
    return recs

@router.get("/competencies", response_model=List[SkillCompetencyOut])
async def get_student_competencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(StudentSkillCompetency, Skill)
        .join(Skill, StudentSkillCompetency.skill_id == Skill.id)
        .where(StudentSkillCompetency.student_id == current_user.id)
    )
    rows = result.all()

    out = []
    for comp, skill in rows:
        label = BKTService.get_status_label(comp.mastery_probability, comp.evidence_count)
        out.append(SkillCompetencyOut(
            skill_id=skill.id,
            skill_name=skill.name,
            category=skill.category,
            mastery_probability=comp.mastery_probability,
            confidence_score=comp.confidence_score,
            evidence_count=comp.evidence_count,
            status_label=label
        ))
    return out

@router.get("/evidence/{skill_id}", response_model=EvidenceDrawerOut)
async def get_evidence_drawer(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = await ArohanService.get_evidence_drawer_data(
        db=db,
        student_id=current_user.id,
        skill_id=skill_id
    )
    if not data:
        raise HTTPException(status_code=404, detail="Skill or evidence record not found")
    return data
