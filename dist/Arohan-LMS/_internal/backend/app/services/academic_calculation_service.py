import math
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.progress import Result, ProgressWeightConfig, StudentProgress, GradingPolicy
from backend.app.services.audit_service import AuditService

class AcademicCalculationService:
    """
    Authoritative, deterministic calculation engine for all institutional academic metrics.
    CRITICAL POLICY: Never use LLMs or probabilistic heuristics for official academic evaluations.
    """

    @staticmethod
    def calculate_percentage(obtained: float, max_marks: float, allow_bonus: bool = False) -> float:
        """
        Calculates percentage with boundary safety and 2-decimal half-up rounding.
        """
        if max_marks is None or max_marks <= 0.0:
            return 0.0
        if obtained is None or math.isnan(obtained):
            return 0.0

        raw_pct = (obtained / max_marks) * 100.0
        rounded_pct = round(raw_pct, 2)

        if not allow_bonus:
            rounded_pct = max(0.0, min(100.0, rounded_pct))
        else:
            rounded_pct = max(0.0, rounded_pct)

        return rounded_pct

    @staticmethod
    def calculate_grade(percentage: float, policy: Optional[GradingPolicy] = None) -> Tuple[str, float]:
        """
        Deterministic grade & grade-point mapping using versioned institutional scale.
        """
        pct = round(percentage, 2)

        min_o = policy.min_o if policy else 90.0
        min_ap = policy.min_ap if policy else 80.0
        min_a = policy.min_a if policy else 70.0
        min_bp = policy.min_bp if policy else 60.0
        min_b = policy.min_b if policy else 55.0
        min_c = policy.min_c if policy else 50.0
        min_p = policy.min_p if policy else 40.0

        if pct >= min_o:
            return ("O", 10.0)
        elif pct >= min_ap:
            return ("A+", 9.0)
        elif pct >= min_a:
            return ("A", 8.0)
        elif pct >= min_bp:
            return ("B+", 7.0)
        elif pct >= min_b:
            return ("B", 6.0)
        elif pct >= min_c:
            return ("C", 5.0)
        elif pct >= min_p:
            return ("P", 4.0)
        else:
            return ("F", 0.0)

    @staticmethod
    def calculate_gpa(grade_points: List[float], credits_list: Optional[List[float]] = None) -> float:
        """
        Calculates SGPA / CGPA using credit-weighted grade points.
        """
        if not grade_points:
            return 0.0

        if not credits_list or len(credits_list) != len(grade_points):
            credits_list = [1.0] * len(grade_points)

        total_credits = sum(credits_list)
        if total_credits <= 0.0:
            return 0.0

        weighted_sum = sum(gp * cr for gp, cr in zip(grade_points, credits_list))
        return round(weighted_sum / total_credits, 2)

    @staticmethod
    def calculate_mcat_score(
        responses: List[Dict[str, Any]],
        questions_dict: Dict[str, Dict[str, Any]],
        negative_marking: bool = False,
        negative_weight: float = 0.25
    ) -> Dict[str, Any]:
        """
        Deterministic scoring for MCAT adaptive and linear examinations.
        """
        total_questions = len(questions_dict)
        attempted = 0
        correct = 0
        incorrect = 0
        unanswered = 0
        cancelled = 0
        raw_score = 0.0
        max_possible_score = 0.0

        for q_id, q_data in questions_dict.items():
            is_cancelled = q_data.get("status") == "CANCELLED"
            q_points = float(q_data.get("points", 1.0))

            if is_cancelled:
                cancelled += 1
                # Cancelled questions grant full points by institutional fairness policy
                raw_score += q_points
                max_possible_score += q_points
                continue

            max_possible_score += q_points
            resp = next((r for r in responses if r.get("question_id") == q_id), None)

            if not resp or resp.get("selected_option_id") is None:
                unanswered += 1
                continue

            attempted += 1
            selected = resp.get("selected_option_id")
            correct_opt = q_data.get("correct_option_id")

            if selected == correct_opt:
                correct += 1
                raw_score += q_points
            else:
                incorrect += 1
                if negative_marking:
                    raw_score -= (q_points * negative_weight)

        final_score = max(0.0, raw_score)
        pct = (final_score / max_possible_score * 100.0) if max_possible_score > 0 else 0.0

        return {
            "total_questions": total_questions,
            "attempted": attempted,
            "correct": correct,
            "incorrect": incorrect,
            "unanswered": unanswered,
            "cancelled": cancelled,
            "raw_score": round(final_score, 2),
            "max_possible_score": round(max_possible_score, 2),
            "percentage": round(pct, 2),
            "passed": pct >= 40.0
        }

    @staticmethod
    def calculate_progress(weights: Dict[str, float], component_scores: Dict[str, float]) -> float:
        """
        Deterministic progress calculation using weighted institutional components.
        """
        total_weight = sum(weights.values())
        if total_weight <= 0.0:
            return 0.0

        weighted_progress = 0.0
        for comp, weight in weights.items():
            score = component_scores.get(comp, 0.0)
            clamped_score = max(0.0, min(100.0, score))
            weighted_progress += (weight / total_weight) * clamped_score

        return round(weighted_progress, 2)

    @classmethod
    async def reconcile_student_progress(
        cls,
        db: AsyncSession,
        student_id: str,
        tolerance: float = 0.05
    ) -> Dict[str, Any]:
        """
        Reconciles stored student progress against authoritative components.
        Detects discrepancies without silent overwriting, logging an audit alert if mismatched.
        """
        p_res = await db.execute(select(StudentProgress).where(StudentProgress.student_id == student_id))
        prog = p_res.scalar_one_or_none()

        if not prog:
            return {"status": "NOT_FOUND", "student_id": student_id}

        # Fetch active weights
        w_res = await db.execute(select(ProgressWeightConfig).where(ProgressWeightConfig.is_active == True))
        config = w_res.scalar_one_or_none()
        weights = {
            "assignment": config.assignment_weight if config else 0.20,
            "assessment": config.assessment_weight if config else 0.25,
            "mcat": config.mcat_weight if config else 0.15,
            "coding": config.coding_weight if config else 0.15,
            "project": config.project_weight if config else 0.15,
            "activity": config.activity_weight if config else 0.10,
        }

        scores = {
            "assignment": prog.assignment_score,
            "assessment": prog.assessment_score,
            "mcat": prog.mcat_score,
            "coding": prog.coding_score,
            "project": prog.project_score,
            "activity": prog.activity_score,
        }

        expected_progress = cls.calculate_progress(weights, scores)
        discrepancy = abs(expected_progress - prog.overall_progress)
        is_consistent = discrepancy <= tolerance

        if not is_consistent:
            # Create DATA_INTEGRITY_ALERT
            await AuditService.log_event(
                db=db,
                action="DATA_INTEGRITY_ALERT",
                user_id=student_id,
                entity_type="StudentProgress",
                entity_id=prog.id,
                details={
                    "stored_progress": prog.overall_progress,
                    "expected_progress": expected_progress,
                    "discrepancy": round(discrepancy, 2),
                    "component_scores": scores
                },
                security_severity="HIGH"
            )

        return {
            "student_id": student_id,
            "stored_progress": prog.overall_progress,
            "expected_progress": expected_progress,
            "discrepancy": round(discrepancy, 2),
            "is_consistent": is_consistent
        }
