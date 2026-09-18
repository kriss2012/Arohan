# Institutional Grading Policy & Versioning Specification

## 1. Versioned Grading Scale

Grading boundaries are managed through versioned policies in the `grading_policies` table rather than hardcoded in source code:

| Grade Letter | Performance Description | Percentage Range | Grade Point |
| :---: | :--- | :---: | :---: |
| **O** | Outstanding | 90.00% – 100.00% | **10.0** |
| **A+** | Excellent | 80.00% – 89.99% | **9.0** |
| **A** | Very Good | 70.00% – 79.99% | **8.0** |
| **B+** | Good | 60.00% – 69.99% | **7.0** |
| **B** | Above Average | 55.00% – 59.99% | **6.0** |
| **C** | Average | 50.00% – 54.99% | **5.0** |
| **P** | Pass | 40.00% – 49.99% | **4.0** |
| **F** | Fail | 0.00% – 39.99% | **0.0** |

---

## 2. Policy Versioning Rule

**Changing future grading thresholds must never retroactively alter historical results.**
- Each published `Result` record stores its computed percentage, grade, and grade point.
- When institutional regulations modify grading boundaries (e.g. from version `v1.0` to `v2.0`), a new `GradingPolicy` record is activated. Past records retain their original assigned grades.
