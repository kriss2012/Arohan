from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.core.database import get_db
from backend.app.models.user import User, StudentProfile
from backend.app.models.evidence import StudentSkillCompetency, Skill
from backend.app.models.arohan import FacultyIntervention
from backend.app.schemas.arohan import InterventionCreate, InterventionOut
from backend.app.api.deps import require_roles

router = APIRouter(prefix="/faculty", tags=["Faculty Console"])

@router.get("/class-summary")
async def get_class_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "SUPER_ADMIN"]))
):
    # Aggregate skill mastery across enrolled students
    skills_res = await db.execute(select(Skill))
    skills = skills_res.scalars().all()

    summary = []
    for sk in skills:
        comp_res = await db.execute(
            select(
                func.avg(StudentSkillCompetency.mastery_probability),
                func.count(StudentSkillCompetency.id)
            ).where(StudentSkillCompetency.skill_id == sk.id)
        )
        avg_mastery, student_count = comp_res.one()
        summary.append({
            "skill_id": sk.id,
            "skill_name": sk.name,
            "category": sk.category,
            "average_mastery": round(avg_mastery or 0.10, 2),
            "assessed_students": student_count or 0,
            "remedial_flag": bool(avg_mastery and avg_mastery < 0.50)
        })
    return summary

@router.post("/interventions")
async def create_intervention(
    payload: InterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["FACULTY", "HOD", "MENTOR", "SUPER_ADMIN"]))
):
    intervention = FacultyIntervention(
        faculty_id=current_user.id,
        student_id=payload.student_id,
        skill_id=payload.skill_id,
        intervention_type=payload.intervention_type,
        notes=payload.notes,
        status="PENDING"
    )
    db.add(intervention)
    await db.commit()
    await db.refresh(intervention)
    return {"message": "Faculty intervention assigned successfully", "id": intervention.id}
