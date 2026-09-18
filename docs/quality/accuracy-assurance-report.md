# Institutional Academic Accuracy Assurance Report

## Executive Summary

This Academic Accuracy Assurance Report documents the mathematical verification, precision analysis, and empirical test results for the calculation engines operating within the **Institute Student Development Platform (ISDP)**.

**Assurance Assessment**: All calculations for official marks, percentages, letter grades, GPAs, progress scores, and MCAT scoring are **100% deterministic**. No machine learning models, probabilistic heuristics, or generative algorithms are involved in generating official student marks.

---

## 1. Mathematical Engine Accuracy Matrix

| Calculation Function | Verified Formula | Precision / Rounding | Boundary Handled | Status |
| :--- | :--- | :--- | :--- | :---: |
| **`calculate_percentage`** | $\operatorname{round}\left(\frac{\text{obtained}}{\text{max}} \times 100, 2\right)$ | 2 decimal places | $0 \le \text{max}$, $0 \le \text{obtained}$, clamped $[0, 100]$ | **PASS** |
| **`calculate_grade`** | Versioned 10-point scale lookup | Monotonic threshold mapping | Exact boundaries ($89.99 \rightarrow \text{A+}$, $90.00 \rightarrow \text{O}$) | **PASS** |
| **`calculate_gpa`** | Credit-weighted grade point sum | 2 decimal places | Credit sum $\le 0$ handled | **PASS** |
| **`calculate_mcat_score`** | $\text{Correct} - \lambda \times \text{Incorrect} + \text{Cancelled}$ | 2 decimal places | Negative penalty factor, cancelled full credit | **PASS** |
| **`calculate_progress`** | Normalized weighted component sum | 2 decimal places | Component score clamping $[0, 100]$ | **PASS** |

---

## 2. Empirical Test Execution Results

All accuracy tests in `backend/tests/test_academic_accuracy_suite.py` passed with 100% success:
- `test_deterministic_percentage_calculation_boundaries`: **PASSED**
- `test_deterministic_grading_policy_boundaries`: **PASSED**
- `test_gpa_credit_weighted_calculation`: **PASSED**
- `test_mcat_scoring_deterministic_engine`: **PASSED**
- `test_golden_dataset_progress_calculation`: **PASSED**

---

**Signed & Approved by:**
Academic Assessment & Examination Board
RC Patel Educational Trust's IMRD, Shirpur
