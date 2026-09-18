# Academic Calculation Accuracy Testing Methodology

## 1. Boundary & Invariant Testing Strategy

Accuracy is verified by property-based and boundary test suites in `backend/tests/test_academic_accuracy_suite.py`:
- Invariant 1: For any valid inputs, $0.0 \le \text{Percentage} \le 100.0$.
- Invariant 2: Grade point mappings are monotonically non-decreasing with respect to percentage.
- Invariant 3: Progress scores match the linear combination of weighted components within floating-point tolerance ($10^{-5}$).

---

## 2. Tested Boundary Conditions

| Scenario | Input Values | Expected Output | Assertion |
| :--- | :--- | :--- | :---: |
| **Lower Boundary** | 0.0 / 100.0 | 0.00%, Grade F (0.0) | **PASS** |
| **Pass Boundary** | 40.0 / 100.0 | 40.00%, Grade P (4.0) | **PASS** |
| **Just Below Pass** | 39.99 / 100.0 | 39.99%, Grade F (0.0) | **PASS** |
| **Outstanding Boundary** | 90.00 / 100.0 | 90.00%, Grade O (10.0) | **PASS** |
| **Just Below Outstanding** | 89.99 / 100.0 | 89.99%, Grade A+ (9.0) | **PASS** |
| **Upper Boundary** | 100.0 / 100.0 | 100.00%, Grade O (10.0) | **PASS** |
| **Zero Maximum Marks** | 50.0 / 0.0 | 0.00% (Defensive Safe) | **PASS** |
| **Negative Maximum Marks**| 50.0 / -10.0 | 0.00% (Defensive Safe) | **PASS** |
| **Negative Marks Obtained**| -5.0 / 100.0 | 0.00% (Clamped) | **PASS** |
| **Over-100 Overflow** | 120.0 / 100.0 | 100.00% (Clamped) | **PASS** |
| **Equal Credit GPA** | Grades: [10.0, 8.0, 9.0] | SGPA = 9.00 | **PASS** |
| **Weighted Credit GPA** | Grades: [10.0, 7.0], Credits: [4, 2] | SGPA = 9.00 | **PASS** |

---

## 3. Golden Dataset Verification

A static golden dataset with pre-calculated institutional benchmarks is evaluated during every automated test run:
- **Golden Student A Component Scores**:
  - Assignment = 80.0, Assessment = 70.0, MCAT = 60.0, Coding = 85.0, Project = 75.0, Activity = 90.0
- **Expected Progress Calculation**:
  $$(0.20 \times 80) + (0.25 \times 70) + (0.15 \times 60) + (0.15 \times 85) + (0.15 \times 75) + (0.10 \times 90) = \mathbf{75.50\%}$$
- **Actual Engine Calculation**: **75.50%** (Exact Match, 0.00 delta).
