from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.models.progress import StudentProgress, ProgressWeightConfig, Result, SkillEvidence, LearningActivity
from backend.app.models.assignment import AssignmentSubmission
from backend.app.models.mcat import MCATAttempt
from backend.app.models.evidence import Skill, StudentSkillCompetency
from backend.app.services.bkt_service import BKTService

class ProgressService:
    @staticmethod
    async def get_active_weights(db: AsyncSession) -> ProgressWeightConfig:
        res = await db.execute(select(ProgressWeightConfig).where(ProgressWeightConfig.is_active == True))
        config = res.scalar_one_or_none()
        if not config:
            config = ProgressWeightConfig(
                institution_id="inst-imrd-01",
                assignment_weight=0.20,
                assessment_weight=0.25,
                mcat_weight=0.15,
                coding_weight=0.15,
                project_weight=0.15,
                activity_weight=0.10
            )
            db.add(config)
            await db.flush()
        return config

    @staticmethod
    async def recalculate_student_progress(
        db: AsyncSession,
        student_id: str,
        subject_id: Optional[str] = None
    ) -> StudentProgress:
        weights = await ProgressService.get_active_weights(db)

        # 1. Assignment Score (average evaluated percentage)
        asgn_res = await db.execute(
            select(func.avg(AssignmentSubmission.percentage))
            .where(
                AssignmentSubmission.student_id == student_id,
                AssignmentSubmission.status == "EVALUATED"
            )
        )
        avg_asgn = asgn_res.scalar() or 0.0

        # 2. MCAT Score (average percentage)
        mcat_res = await db.execute(
            select(func.avg(MCATAttempt.score_percentage))
            .where(
                MCATAttempt.student_id == student_id,
                MCATAttempt.status.in_(["AUTO_EVALUATED", "FINALIZED"])
            )
        )
        avg_mcat = mcat_res.scalar() or 0.0

        # 3. Assessment Score (internal tests)
        assess_res = await db.execute(
            select(func.avg(Result.percentage))
            .where(
                Result.student_id == student_id,
                Result.published == True
            )
        )
        avg_assess = assess_res.scalar() or (avg_asgn if avg_asgn > 0 else 75.0)

        # 4. Coding & Project baselines
        coding_score = 80.0
        project_score = 85.0
        activity_score = 90.0

        # Weighted calculation
        overall = (
            (avg_asgn * weights.assignment_weight) +
            (avg_assess * weights.assessment_weight) +
            (avg_mcat * weights.mcat_weight) +
            (coding_score * weights.coding_weight) +
            (project_score * weights.project_weight) +
            (activity_score * weights.activity_weight)
        )
        overall = round(max(0.0, min(100.0, overall)), 2)

        # Upsert StudentProgress
        prog_res = await db.execute(
            select(StudentProgress).where(
                StudentProgress.student_id == student_id,
                StudentProgress.subject_id == subject_id
            )
        )
        progress = prog_res.scalar_one_or_none()
        if not progress:
            progress = StudentProgress(
                student_id=student_id,
                subject_id=subject_id,
                overall_progress=overall,
                completion_percentage=min(100.0, overall + 5.0),
                assignment_score=round(avg_asgn, 1),
                mcat_score=round(avg_mcat, 1),
                assessment_score=round(avg_assess, 1),
                coding_score=coding_score,
                project_score=project_score,
                activity_score=activity_score,
                last_activity_at=datetime.now(timezone.utc)
            )
            db.add(progress)
        else:
            progress.overall_progress = overall
            progress.assignment_score = round(avg_asgn, 1)
            progress.mcat_score = round(avg_mcat, 1)
            progress.assessment_score = round(avg_assess, 1)
            progress.last_activity_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(progress)
        return progress

    @staticmethod
    async def record_skill_evidence(
        db: AsyncSession,
        student_id: str,
        skill_id: str,
        source_type: str,
        source_id: str,
        score: float,
        confidence: float = 0.85
    ) -> SkillEvidence:
        normalized = max(0.0, min(1.0, score / 100.0 if score > 1.0 else score))

        evidence = SkillEvidence(
            student_id=student_id,
            skill_id=skill_id,
            source_type=source_type,
            source_id=source_id,
            score=score,
            normalized_score=normalized,
            confidence=confidence
        )
        db.add(evidence)

        # Also update Bayesian Knowledge Tracing for this skill
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
                evidence_count=0
            )
            db.add(comp)
            await db.flush()

        is_success = normalized >= 0.50
        comp.mastery_probability = BKTService.update_mastery(comp.mastery_probability, is_success)
        comp.evidence_count += 1
        if is_success:
            comp.correct_count += 1
        else:
            comp.incorrect_count += 1
        comp.last_updated = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(evidence)
        return evidence
