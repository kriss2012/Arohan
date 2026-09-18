import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.curriculum import Subject, Unit, Topic, Resource, StudentTopicProgress
from backend.app.models.evidence import StudentEvent
from backend.app.models.user import User
from backend.app.schemas.curriculum import SubjectOut, ProgressUpdateRequest
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])

@router.get("/tree", response_model=List[SubjectOut])
async def get_curriculum_tree(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Fetch subjects with nested units, topics, and resources
    result = await db.execute(
        select(Subject)
        .options(
            selectinload(Subject.units)
            .selectinload(Unit.topics)
            .selectinload(Topic.resources)
        )
    )
    subjects = result.scalars().all()
    return subjects

@router.post("/topics/{topic_id}/progress")
async def update_topic_progress(
    topic_id: str,
    payload: ProgressUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if topic exists
    top_res = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = top_res.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    prog_res = await db.execute(
        select(StudentTopicProgress).where(
            StudentTopicProgress.student_id == current_user.id,
            StudentTopicProgress.topic_id == topic_id
        )
    )
    progress = prog_res.scalar_one_or_none()
    if not progress:
        progress = StudentTopicProgress(
            student_id=current_user.id,
            topic_id=topic_id,
            status=payload.status,
            time_spent_seconds=payload.time_spent_seconds
        )
        db.add(progress)
    else:
        progress.status = payload.status
        progress.time_spent_seconds += payload.time_spent_seconds

    # Emit learning activity event to Evidence Engine
    if payload.status == "COMPLETED":
        event = StudentEvent(
            student_id=current_user.id,
            event_type="StudentCompletedTopic",
            source="CURRICULUM",
            metadata_json=json.dumps({
                "topic_id": topic_id,
                "topic_title": topic.title,
                "time_spent_seconds": payload.time_spent_seconds
            })
        )
        db.add(event)

    await db.commit()
    return {"message": "Progress recorded successfully", "status": payload.status}
