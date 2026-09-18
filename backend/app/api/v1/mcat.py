import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.database import get_db
from backend.app.models.mcat import MCATExam, MCATAttempt, Question, QuestionOption, MCATIntegrityEvent, MCATResponse
from backend.app.models.user import User
from backend.app.schemas.mcat import (
    ExamSummaryOut, AttemptStartRequest, AttemptOut,
    ResponseSaveRequest, IntegrityEventCreate, ScoreResultOut,
    QuestionOut, QuestionOptionOut, AttemptResponseOut
)
from backend.app.services.mcat_service import MCATService
from backend.app.services.integrity_service import IntegrityService
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/mcat", tags=["MCAT Assessment"])

@router.get("/exams", response_model=List[ExamSummaryOut])
async def list_exams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(MCATExam).where(MCATExam.is_published == True)
    )
    exams = result.scalars().all()
    
    out = []
    for ex in exams:
        out.append(ExamSummaryOut(
            id=ex.id,
            title=ex.title,
            exam_code=ex.exam_code,
            mode=ex.mode,
            total_questions=10,
            time_limit_minutes=15,
            is_published=ex.is_published
        ))
    return out

@router.post("/attempts/start", response_model=AttemptOut)
async def start_or_resume_attempt(
    payload: AttemptStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = await MCATService.start_or_resume_attempt(
        db=db,
        exam_id=payload.exam_id,
        student_id=current_user.id
    )

    # Fetch exam title
    exam_res = await db.execute(select(MCATExam).where(MCATExam.id == payload.exam_id))
    exam = exam_res.scalar_one_or_none()

    # Load all approved questions with options (without exposing is_correct)
    q_res = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.status == "APPROVED")
    )
    questions = q_res.scalars().all()

    # Format questions safely for client
    q_out = []
    for q in questions:
        opts = [
            QuestionOptionOut(id=opt.id, option_key=opt.option_key, option_text=opt.option_text)
            for opt in q.options
        ]
        q_out.append(QuestionOut(
            id=q.id,
            category=q.category,
            subcategory=q.subcategory,
            difficulty=q.difficulty,
            question_type=q.question_type,
            question_text=q.question_text,
            options=opts
        ))

    # Fetch existing responses if any
    resp_res = await db.execute(
        select(MCATResponse).where(MCATResponse.attempt_id == attempt.id)
    )
    saved_resps = [
        AttemptResponseOut(
            question_id=r.question_id,
            selected_option_id=r.selected_option_id,
            is_marked_for_review=r.is_marked_for_review
        )
        for r in resp_res.scalars().all()
    ]

    return AttemptOut(
        id=attempt.id,
        exam_id=attempt.exam_id,
        exam_title=exam.title if exam else "MCAT Examination",
        status=attempt.status,
        remaining_seconds=attempt.remaining_seconds,
        total_questions=len(q_out),
        questions=q_out,
        saved_responses=saved_resps
    )

@router.post("/attempts/{attempt_id}/save-response")
async def save_response(
    attempt_id: str,
    payload: ResponseSaveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Anomaly check on rapid answer submission
    if payload.response_time_seconds > 0 and payload.response_time_seconds < 2.0:
        # Record rapid submission signal
        ev = MCATIntegrityEvent(
            attempt_id=attempt_id,
            event_type="ANOMALY_TIME",
            severity="LOW",
            details_json=json.dumps({"question_id": payload.question_id, "time_seconds": payload.response_time_seconds})
        )
        db.add(ev)

    await MCATService.save_response(
        db=db,
        attempt_id=attempt_id,
        student_id=current_user.id,
        question_id=payload.question_id,
        selected_option_id=payload.selected_option_id,
        is_marked_for_review=payload.is_marked_for_review,
        response_time_seconds=payload.response_time_seconds
    )
    return {"status": "saved", "question_id": payload.question_id}

@router.post("/attempts/{attempt_id}/integrity-event")
async def log_integrity_event(
    attempt_id: str,
    payload: IntegrityEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    severity, note = IntegrityService.classify_signal(payload.event_type, payload.details)

    ev = MCATIntegrityEvent(
        attempt_id=attempt_id,
        event_type=payload.event_type,
        severity=severity,
        details_json=json.dumps({"note": note, "details": payload.details or {}})
    )
    db.add(ev)

    # Increment attempt counter
    att_res = await db.execute(select(MCATAttempt).where(MCATAttempt.id == attempt_id))
    attempt = att_res.scalar_one_or_none()
    if attempt:
        attempt.integrity_signal_count += 1

    await db.commit()
    return {"message": "Integrity signal recorded", "severity": severity}

@router.post("/attempts/{attempt_id}/submit", response_model=ScoreResultOut)
async def submit_attempt(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attempt = await MCATService.submit_and_evaluate_attempt(
        db=db,
        attempt_id=attempt_id,
        student_id=current_user.id
    )

    cat_scores = json.loads(attempt.category_scores_json or "{}")

    return ScoreResultOut(
        attempt_id=attempt.id,
        status=attempt.status,
        score_raw=attempt.score_raw,
        score_percentage=attempt.score_percentage,
        total_correct=attempt.total_correct,
        total_incorrect=attempt.total_incorrect,
        total_unanswered=attempt.total_unanswered,
        category_scores=cat_scores,
        integrity_signal_count=attempt.integrity_signal_count
    )
