from typing import Tuple, Dict, Any

class BKTService:
    """
    Standard Bayesian Knowledge Tracing (Corbett & Anderson)
    Latent Knowledge Model:
      P(L0): Prior probability of knowing the skill
      P(T): Transition/learning probability
      P(S): Slip probability (knows, but answers wrong)
      P(G): Guess probability (does not know, but guesses right)
    """

    @staticmethod
    def update_mastery(
        p_l_prev: float,
        is_correct: bool,
        p_t: float = 0.15,
        p_s: float = 0.10,
        p_g: float = 0.20
    ) -> float:
        # Clamp bounds to prevent division by zero
        p_l_prev = max(0.001, min(0.999, p_l_prev))
        p_s = max(0.01, min(0.49, p_s))
        p_g = max(0.01, min(0.49, p_g))
        p_t = max(0.01, min(0.50, p_t))

        # 1. Update belief based on observation
        if is_correct:
            numerator = p_l_prev * (1.0 - p_s)
            denominator = numerator + ((1.0 - p_l_prev) * p_g)
        else:
            numerator = p_l_prev * p_s
            denominator = numerator + ((1.0 - p_l_prev) * (1.0 - p_g))

        p_l_given_obs = numerator / max(denominator, 1e-9)

        # 2. Account for transition (learning that occurred during the opportunity)
        p_l_next = p_l_given_obs + ((1.0 - p_l_given_obs) * p_t)

        return round(max(0.01, min(0.99, p_l_next)), 4)

    @staticmethod
    def calculate_skill_gap(
        mastery_probability: float,
        recent_error_rate: float,
        assessment_weight: float = 0.70,
        coding_weight: float = 0.50,
        recency_factor: float = 0.80,
        evidence_count: int = 0
    ) -> Tuple[float, str]:
        """
        GapScore = 0.45 * (1 - mastery) + 0.20 * error_rate + 0.15 * assess_wt + 0.10 * code_wt + 0.10 * recency
        Returns (GapScore, StatusLabel)
        """
        if evidence_count < 3:
            return 0.0, "INSUFFICIENT_EVIDENCE"

        mastery_gap = 1.0 - mastery_probability
        gap_score = (
            (0.45 * mastery_gap) +
            (0.20 * recent_error_rate) +
            (0.15 * assessment_weight) +
            (0.10 * coding_weight) +
            (0.10 * recency_factor)
        )
        gap_score = round(max(0.0, min(1.0, gap_score)), 4)

        if mastery_probability < 0.40:
            status = "PREREQUISITE_LEARN"
        elif mastery_probability < 0.70:
            status = "GUIDED_PRACTICE"
        elif mastery_probability < 0.85:
            status = "MIXED_PRACTICE"
        else:
            status = "VALIDATION_ADVANCED"

        return gap_score, status

    @staticmethod
    def get_status_label(mastery_probability: float, evidence_count: int) -> str:
        if evidence_count < 3:
            return "Insufficient Evidence"
        if mastery_probability < 0.40:
            return "Novice (Gap Detected)"
        if mastery_probability < 0.70:
            return "Developing"
        if mastery_probability < 0.85:
            return "Proficient"
        return "Mastered"
