# Deterministic Academic Calculations Specification

## 1. Authoritative Calculation Principle

**CRITICAL MANDATE: NEVER USE AN LLM OR PROBABILISTIC MODEL TO CALCULATE OR AUTHORITATIVELY DETERMINE OFFICIAL MARKS, PERCENTAGES, GRADES, GPAS, MCAT SCORES, OR PROGRESS METRICS.**

All academic scoring in ISDP is strictly deterministic, version-controlled, and implemented in the authoritative service:
`backend.app.services.academic_calculation_service.AcademicCalculationService`

---

## 2. Mathematical Formulas & Rounding Rules

### A. Percentage Calculation
$$\text{Percentage} = \operatorname{round}\left(\frac{\text{Marks Obtained}}{\text{Maximum Marks}} \times 100.0, \, 2\right)$$

- **Rounding Standard**: Round half-up to exactly 2 decimal places.
- **Boundaries**: Clamped strictly between `0.00%` and `100.00%` (unless institutional policy explicitly permits bonus marks).
- **Edge Cases**:
  - If $\text{Maximum Marks} \le 0.0$: Returns `0.00%`.
  - If $\text{Marks Obtained}$ is `None` or `NaN`: Returns `0.00%`.
  - If $\text{Marks Obtained} < 0.0$: Clamped to `0.00%`.

### B. Grade Point Average (SGPA / CGPA)
$$\text{GPA} = \operatorname{round}\left(\frac{\sum_{i=1}^n (\text{Grade Point}_i \times \text{Credits}_i)}{\sum_{i=1}^n \text{Credits}_i}, \, 2\right)$$

- If course credits are unassigned, equal weighting ($\text{Credits}_i = 1.0$) is applied.
- If total credits $\le 0.0$, returns `0.00`.

---

## 3. Decimal Precision & Database Types

- Internal storage uses SQL `NUMERIC(7,2)` or IEEE 754 float sanitized at the application service boundary.
- No binary floating-point rounding artifacts are permitted to leak into student transcripts.
