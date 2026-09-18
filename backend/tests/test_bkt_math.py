import pytest
from backend.app.services.bkt_service import BKTService

def test_bkt_mastery_increases_on_correct():
    initial_p = 0.10
    updated_p = BKTService.update_mastery(initial_p, is_correct=True)
    assert updated_p > initial_p, "Mastery probability must increase after a correct answer"

def test_bkt_mastery_decreases_on_incorrect():
    initial_p = 0.70
    updated_p = BKTService.update_mastery(initial_p, is_correct=False)
    assert updated_p < initial_p, "Mastery probability must decrease after an incorrect answer"

def test_bkt_monotone_convergence():
    p = 0.10
    for _ in range(5):
        p = BKTService.update_mastery(p, is_correct=True)
    assert p >= 0.80, f"Repeated correct answers should lead towards high mastery, got {p}"

def test_skill_gap_insufficient_evidence():
    gap_score, status = BKTService.calculate_skill_gap(
        mastery_probability=0.20,
        recent_error_rate=0.80,
        evidence_count=2
    )
    assert status == "INSUFFICIENT_EVIDENCE", "Fewer than 3 observations must report INSUFFICIENT_EVIDENCE"
    assert gap_score == 0.0

def test_skill_gap_prerequisite_recommendation():
    gap_score, status = BKTService.calculate_skill_gap(
        mastery_probability=0.30,
        recent_error_rate=0.70,
        evidence_count=8
    )
    assert status == "PREREQUISITE_LEARN"
    assert gap_score > 0.40
