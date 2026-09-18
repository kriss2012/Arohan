import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from backend.app.models.mcat import MCATExam, MCATAttempt, MCATResponse, Question, QuestionOption, MCATIntegrityEvent
from backend.app.models.evidence import Skill, StudentSkillCompetency, StudentEvent
from backend.app.services.bkt_service import BKTService
from backend.app.services.integrity_service import IntegrityService

class MCATService:
    # 11 State Lifecycle Definitions
    VALID_TRANSITIONS = {
        "CREATED": ["AUTHORIZED"],
        "AUTHORIZED": ["STARTED"],
        "STARTED": ["PAUSED", "INTERRUPTED", "SUBMITTED"],
        "PAUSED": ["RESUMED", "SUBMITTED"],
        "INTERRUPTED": ["RESUMED", "SUBMITTED"],
        "RESUMED": ["STARTED"],
        "SUBMITTED": ["AUTO_EVALUATED"],
        "AUTO_EVALUATED": ["UNDER_REVIEW", "FINALIZED"],
        "UNDER_REVIEW": ["FINALIZED", "CANCELLED"],
        "FINALIZED": [],
        "CANCELLED": []
    }

    @staticmethod
    def validate_transition(current_state: str, target_state: str) -> bool:
        allowed = MCATService.VALID_TRANSITIONS.get(current_state, [])
        return target_state in allowed

    @staticmethod
    async def start_or_resume_attempt(
        db: AsyncSession,
        exam_id: str,
        student_id: str
    ) -> MCATAttempt:
        # Check for existing attempt
        result = await db.execute(
            select(MCATAttempt).where(
                MCATAttempt.exam_id == exam_id,
                MCATAttempt.student_id == student_id
            )
        )
        attempt = result.scalar_one_or_none()

        if not attempt:
            # Create attempt
            exam_res = await db.execute(select(MCATExam).where(MCATExam.id == exam_id))
            exam = exam_res.scalar_one_or_none()
            if not exam:
                raise HTTPException(status_code=404, detail="MCAT Exam not found")
            
            attempt = MCATAttempt(
                exam_id=exam_id,
                student_id=student_id,
                status="STARTED",
                started_at=datetime.now(timezone.utc),
                remaining_seconds=1800 # 30 mins
            )
            db.add(attempt)
            await db.flush()

            # Record event in evidence log
            event = StudentEvent(
                student_id=student_id,
                event_type="StudentStartedMCAT",
                source="MCAT",
                metadata_json=json.dumps({"exam_id": exam_id, "attempt_id": attempt.id})
            )
            db.add(event)
            await db.commit()
            await db.refresh(attempt)
            return attempt

        # If existing and can be resumed
        if attempt.status in ["PAUSED", "INTERRUPTED"]:
            attempt.status = "STARTED"
            await db.commit()
            await db.refresh(attempt)
            return attempt
        
        if attempt.status in ["STARTED"]:
            return attempt

        if attempt.status in ["SUBMITTED", "AUTO_EVALUATED", "FINALIZED"]:
            raise HTTPException(status_code=400, detail="This exam attempt has already been submitted.")

        raise HTTPException(status_code=400, detail=f"Cannot start attempt from state {attempt.status}")

    @staticmethod
    async def save_response(
        db: AsyncSession,
        attempt_id: str,
        student_id: str,
        question_id: str,
        selected_option_id: Optional[str],
        is_marked_for_review: bool,
        response_time_seconds: float
    ) -> MCATResponse:
        result = await db.execute(select(MCATAttempt).where(MCATAttempt.id == attempt_id))
        attempt = result.scalar_one_or_none()
        if not attempt or attempt.student_id != student_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to exam attempt")

        if attempt.status not in ["STARTED", "RESUMED"]:
            raise HTTPException(status_code=400, detail=f"Cannot save response in attempt state {attempt.status}")

        # Find or create response
        resp_res = await db.execute(
            select(MCATResponse).where(
                MCATResponse.attempt_id == attempt_id,
                MCATResponse.question_id == question_id
            )
        )
        response = resp_res.scalar_one_or_none()
        if not response:
            response = MCATResponse(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_option_id=selected_option_id,
                is_marked_for_review=is_marked_for_review,
                response_time_seconds=response_time_seconds
            )
            db.add(response)
        else:
            response.selected_option_id = selected_option_id
            response.is_marked_for_review = is_marked_for_review
            response.response_time_seconds = response_time_seconds

        await db.commit()
        await db.refresh(response)
        return response

    @staticmethod
    async def submit_and_evaluate_attempt(
        db: AsyncSession,
        attempt_id: str,
        student_id: str
    ) -> MCATAttempt:
        result = await db.execute(select(MCATAttempt).where(MCATAttempt.id == attempt_id))
        attempt = result.scalar_one_or_none()
        if not attempt or attempt.student_id != student_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to exam attempt")

        if attempt.status in ["SUBMITTED", "AUTO_EVALUATED", "FINALIZED"]:
            return attempt

        # Transition to SUBMITTED
        attempt.status = "SUBMITTED"
        attempt.submitted_at = datetime.now(timezone.utc)
        await db.flush()

        # Auto-Evaluate
        responses_res = await db.execute(
            select(MCATResponse).where(MCATResponse.attempt_id == attempt_id)
        )
        responses = responses_res.scalars().all()

        total_correct = 0
        total_incorrect = 0
        category_stats: Dict[str, Dict[str, int]] = {}

        for resp in responses:
            q_res = await db.execute(select(Question).where(Question.id == resp.question_id))
            question = q_res.scalar_one_or_none()
            if not question:
                continue

            category = question.category
            if category not in category_stats:
                category_stats[category] = {"correct": 0, "total": 0}
            category_stats[category]["total"] += 1

            # Check correctness
            if resp.selected_option_id:
                opt_res = await db.execute(
                    select(QuestionOption).where(QuestionOption.id == resp.selected_option_id)
                )
                option = opt_res.scalar_one_or_none()
                is_correct = bool(option and option.is_correct)
                resp.is_correct = is_correct

                if is_correct:
                    total_correct += 1
                    category_stats[category]["correct"] += 1
                else:
                    total_incorrect += 1

                # Update BKT for this skill
                await MCATService._update_bkt_for_skill(
                    db=db,
                    student_id=student_id,
                    skill_id=question.skill_id,
                    is_correct=is_correct
                )

        total_answered = total_correct + total_incorrect
        total_questions = max(len(responses), 1)
        score_raw = float(total_correct)
        score_pct = round((score_raw / total_questions) * 100.0, 2)

        # Build category percentage map
        category_percentages = {}
        for cat, val in category_stats.items():
            tot = val["total"]
            corr = val["correct"]
            category_percentages[cat] = round((corr / tot) * 100.0, 1) if tot > 0 else 0.0

        attempt.score_raw = score_raw
        attempt.score_percentage = score_pct
        attempt.total_correct = total_correct
        attempt.total_incorrect = total_incorrect
        attempt.total_unanswered = max(0, total_questions - total_answered)
        attempt.category_scores_json = json.dumps(category_percentages)
        attempt.status = "AUTO_EVALUATED"

        # Record submission event in evidence stream
        event = StudentEvent(
            student_id=student_id,
            event_type="StudentCompletedMCAT",
            source="MCAT",
            metadata_json=json.dumps({
                "attempt_id": attempt_id,
                "score_percentage": score_pct,
                "category_breakdown": category_percentages
            })
        )
        db.add(event)

        await db.commit()
        await db.refresh(attempt)
        return attempt

    @staticmethod
    async def _update_bkt_for_skill(
        db: AsyncSession,
        student_id: str,
        skill_id: str,
        is_correct: bool
    ) -> None:
        comp_res = await db.execute(
            select(StudentSkillCompetency).where(
                StudentSkillCompetency.student_id == student_id,
                StudentSkillCompetency.skill_id == skill_id
            )
        )
        comp = comp_res.scalar_one_or_none()
        if not comp:
            comp = StudentSkillCompetency(
                student_id=student_id,
                skill_id=skill_id,
                mastery_probability=0.10,
                evidence_count=0,
                correct_count=0,
                incorrect_count=0
            )
            db.add(comp)
            await db.flush()

        prev_mastery = comp.mastery_probability
        new_mastery = BKTService.update_mastery(prev_mastery, is_correct)
        comp.mastery_probability = new_mastery
        comp.evidence_count += 1
        if is_correct:
            comp.correct_count += 1
        else:
            comp.incorrect_count += 1
        
        # Confidence increases with more evidence
        comp.confidence_score = round(min(0.98, 0.40 + (comp.evidence_count * 0.08)), 2)
        comp.last_updated = datetime.now(timezone.utc)
