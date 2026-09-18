from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.models.evidence import Skill, StudentSkillCompetency, StudentEvent
from backend.app.models.arohan import Recommendation
from backend.app.services.bkt_service import BKTService

class ArohanService:
    @staticmethod
    async def get_or_generate_recommendations(
        db: AsyncSession,
        student_id: str
    ) -> List[Dict[str, Any]]:
        # Fetch all student skill competencies
        result = await db.execute(
            select(StudentSkillCompetency, Skill)
            .join(Skill, StudentSkillCompetency.skill_id == Skill.id)
            .where(StudentSkillCompetency.student_id == student_id)
        )
        rows = result.all()

        recommendations = []
        # Find skills with gap
        for comp, skill in rows:
            if comp.evidence_count < 1:
                continue

            error_rate = (comp.incorrect_count / max(1, comp.evidence_count))
            gap_score, action_type = BKTService.calculate_skill_gap(
                mastery_probability=comp.mastery_probability,
                recent_error_rate=error_rate,
                evidence_count=comp.evidence_count
            )

            # Recommend if gap is significant and not yet mastered
            if comp.mastery_probability < 0.75:
                # Generate explainable rationale
                rationale = (
                    f"Recommended because current estimated mastery is {int(comp.mastery_probability * 100)}% "
                    f"with {comp.incorrect_count} incorrect answers recorded out of {comp.evidence_count} attempts. "
                    f"Calculated Gap Score: {gap_score:.2f}."
                )

                if action_type == "PREREQUISITE_LEARN":
                    title = f"Review Prerequisite Fundamentals: {skill.name}"
                    summary = f"Your mastery on {skill.name} is in the foundational stage ({int(comp.mastery_probability * 100)}%). Review key concepts before next assessment."
                else:
                    title = f"Targeted Guided Practice: {skill.name}"
                    summary = f"Solve 10 practice problems in {skill.name} to reinforce accuracy."

                recommendations.append({
                    "id": f"rec-{skill.id[:8]}",
                    "skill_id": skill.id,
                    "skill_name": skill.name,
                    "category": skill.category,
                    "action_type": action_type,
                    "title": title,
                    "evidence_summary": summary,
                    "mathematical_rationale": rationale,
                    "why_endpoint": f"/api/v1/arohan/evidence/{skill.id}",
                    "gap_score": gap_score,
                    "is_completed": False
                })

        # Sort by gap_score descending, limit to Top 4 to avoid overwhelming student
        recommendations.sort(key=lambda x: x["gap_score"], reverse=True)
        return recommendations[:4]

    @staticmethod
    async def get_evidence_drawer_data(
        db: AsyncSession,
        student_id: str,
        skill_id: str
    ) -> Dict[str, Any]:
        # Skill details
        s_res = await db.execute(select(Skill).where(Skill.id == skill_id))
        skill = s_res.scalar_one_or_none()
        if not skill:
            return {}

        # Competency
        c_res = await db.execute(
            select(StudentSkillCompetency).where(
                StudentSkillCompetency.student_id == student_id,
                StudentSkillCompetency.skill_id == skill_id
            )
        )
        comp = c_res.scalar_one_or_none()

        mastery = comp.mastery_probability if comp else 0.10
        confidence = comp.confidence_score if comp else 0.40
        ev_count = comp.evidence_count if comp else 0
        correct_count = comp.correct_count if comp else 0
        incorrect_count = comp.incorrect_count if comp else 0

        error_rate = (incorrect_count / max(1, ev_count)) if ev_count > 0 else 0.0
        gap_score, _ = BKTService.calculate_skill_gap(
            mastery_probability=mastery,
            recent_error_rate=error_rate,
            evidence_count=ev_count
        )

        # Recent events for student
        ev_res = await db.execute(
            select(StudentEvent)
            .where(StudentEvent.student_id == student_id)
            .order_by(desc(StudentEvent.timestamp))
            .limit(5)
        )
        recent_events = [
            {
                "event_type": ev.event_type,
                "source": ev.source,
                "timestamp": ev.timestamp.isoformat()
            }
            for ev in ev_res.scalars().all()
        ]

        logic = (
            f"BKT Posterior Mastery: {mastery:.2f} (Confidence: {int(confidence*100)}%). "
            f"Evidence Logged: {ev_count} items ({correct_count} correct, {incorrect_count} incorrect). "
            f"Gap Score: {gap_score:.3f} = 0.45*(1 - {mastery:.2f}) + 0.20*({error_rate:.2f}) + weights."
        )

        return {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "category": skill.category,
            "mastery_probability": mastery,
            "confidence_score": confidence,
            "evidence_count": ev_count,
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "gap_score": gap_score,
            "recommendation_logic": logic,
            "recent_evidence_events": recent_events
        }
