import pytest
from backend.app.services.academic_calculation_service import AcademicCalculationService
from backend.app.models.progress import GradingPolicy

def test_deterministic_percentage_calculation_boundaries():
    """
    Tests exact decimal rounding and boundaries for percentage calculation.
    """
    calc = AcademicCalculationService.calculate_percentage

    # 1. Standard boundaries
    assert calc(0.0, 100.0) == 0.0
    assert calc(100.0, 100.0) == 100.0
    assert calc(82.0, 100.0) == 82.0
    assert calc(33.3333, 100.0) == 33.33
    assert calc(66.6666, 100.0) == 66.67
    assert calc(99.999, 100.0) == 100.0

    # 2. Non-standard maximum marks
    assert calc(45.0, 50.0) == 90.0
    assert calc(17.5, 25.0) == 70.0

    # 3. Defensive zero and negative inputs
    assert calc(50.0, 0.0) == 0.0, "Zero maximum marks must safely return 0.0"
    assert calc(50.0, -10.0) == 0.0, "Negative maximum marks must safely return 0.0"
    assert calc(-5.0, 100.0) == 0.0, "Negative obtained marks must be clamped to 0.0"
    assert calc(None, 100.0) == 0.0, "None marks must safely return 0.0"

    # 4. Overflow clamping
    assert calc(120.0, 100.0) == 100.0, "Standard calculation must clamp to 100.0 max"
    assert calc(120.0, 100.0, allow_bonus=True) == 120.0, "Bonus marks policy allows overflow"

def test_deterministic_grading_policy_boundaries():
    """
    Tests exact 10-point scale threshold boundaries.
    """
    grade = AcademicCalculationService.calculate_grade

    # O: 90.00% - 100%
    assert grade(100.0) == ("O", 10.0)
    assert grade(90.00) == ("O", 10.0)

    # A+: 80.00% - 89.99%
    assert grade(89.99) == ("A+", 9.0)
    assert grade(85.00) == ("A+", 9.0)
    assert grade(80.00) == ("A+", 9.0)

    # A: 70.00% - 79.99%
    assert grade(79.99) == ("A", 8.0)
    assert grade(75.00) == ("A", 8.0)
    assert grade(70.00) == ("A", 8.0)

    # B+: 60.00% - 69.99%
    assert grade(69.99) == ("B+", 7.0)
    assert grade(60.00) == ("B+", 7.0)

    # B: 55.00% - 59.99%
    assert grade(59.99) == ("B", 6.0)
    assert grade(55.00) == ("B", 6.0)

    # C: 50.00% - 54.99%
    assert grade(54.99) == ("C", 5.0)
    assert grade(50.00) == ("C", 5.0)

    # P: 40.00% - 49.99%
    assert grade(49.99) == ("P", 4.0)
    assert grade(40.00) == ("P", 4.0)

    # F: < 40.00%
    assert grade(39.99) == ("F", 0.0)
    assert grade(0.0) == ("F", 0.0)

def test_gpa_credit_weighted_calculation():
    """
    Tests credit-weighted SGPA calculation.
    """
    calc_gpa = AcademicCalculationService.calculate_gpa

    # Equal credits
    assert calc_gpa([10.0, 8.0, 9.0]) == 9.0

    # Weighted credits: Course A (4 credits, 10.0), Course B (2 credits, 7.0)
    # (4*10 + 2*7) / 6 = (40 + 14) / 6 = 54 / 6 = 9.00
    assert calc_gpa([10.0, 7.0], [4.0, 2.0]) == 9.0

    # Weighted credits with decimals
    # Course 1 (3 credits, 9.0) -> 27
    # Course 2 (4 credits, 8.0) -> 32
    # Course 3 (3 credits, 7.0) -> 21
    # Total = 80 / 10 = 8.00
    assert calc_gpa([9.0, 8.0, 7.0], [3.0, 4.0, 3.0]) == 8.0

def test_mcat_scoring_deterministic_engine():
    """
    Tests MCAT scoring under various condition matrix (correct, incorrect, cancelled, negative marking).
    """
    questions = {
        "q1": {"points": 1.0, "correct_option_id": "opt-1", "status": "ACTIVE"},
        "q2": {"points": 1.0, "correct_option_id": "opt-2", "status": "ACTIVE"},
        "q3": {"points": 1.0, "correct_option_id": "opt-3", "status": "ACTIVE"},
        "q4": {"points": 1.0, "correct_option_id": "opt-4", "status": "ACTIVE"},
        "q5": {"points": 1.0, "correct_option_id": "opt-5", "status": "CANCELLED"}, # Cancelled question
    }

    # Scenario A: All answered correctly
    resp_a = [
        {"question_id": "q1", "selected_option_id": "opt-1"},
        {"question_id": "q2", "selected_option_id": "opt-2"},
        {"question_id": "q3", "selected_option_id": "opt-3"},
        {"question_id": "q4", "selected_option_id": "opt-4"},
    ]
    res_a = AcademicCalculationService.calculate_mcat_score(resp_a, questions)
    assert res_a["raw_score"] == 5.0
    assert res_a["percentage"] == 100.0
    assert res_a["cancelled"] == 1
    assert res_a["passed"] is True

    # Scenario B: Negative marking enabled (2 correct, 2 incorrect, 1 cancelled)
    resp_b = [
        {"question_id": "q1", "selected_option_id": "opt-1"}, # +1
        {"question_id": "q2", "selected_option_id": "opt-wrong"}, # -0.25
        {"question_id": "q3", "selected_option_id": "opt-wrong"}, # -0.25
        {"question_id": "q4", "selected_option_id": "opt-4"}, # +1
        # q5 cancelled -> +1
    ]
    # Total = 1 - 0.25 - 0.25 + 1 + 1 = 2.50 out of 5.0 = 50.0%
    res_b = AcademicCalculationService.calculate_mcat_score(resp_b, questions, negative_marking=True, negative_weight=0.25)
    assert res_b["raw_score"] == 2.5
    assert res_b["percentage"] == 50.0
    assert res_b["passed"] is True

def test_golden_dataset_progress_calculation():
    """
    Tests Golden Dataset for Progress calculation against pre-computed verified baseline.
    """
    # Standard institutional weights:
    # Assignment: 20%, Assessment: 25%, MCAT: 15%, Coding: 15%, Project: 15%, Activity: 10%
    weights = {
        "assignment": 0.20,
        "assessment": 0.25,
        "mcat": 0.15,
        "coding": 0.15,
        "project": 0.15,
        "activity": 0.10
    }

    # Golden Student A scores:
    # Assignment: 80.0
    # Assessment: 70.0
    # MCAT: 60.0
    # Coding: 85.0
    # Project: 75.0
    # Activity: 90.0
    # Expected: (0.20*80) + (0.25*70) + (0.15*60) + (0.15*85) + (0.15*75) + (0.10*90)
    #         = 16.0 + 17.5 + 9.0 + 12.75 + 11.25 + 9.0
    #         = 75.50%
    scores_a = {
        "assignment": 80.0,
        "assessment": 70.0,
        "mcat": 60.0,
        "coding": 85.0,
        "project": 75.0,
        "activity": 90.0
    }
    progress = AcademicCalculationService.calculate_progress(weights, scores_a)
    assert progress == 75.50, f"Expected 75.50, got {progress}"
