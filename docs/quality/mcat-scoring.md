# MCAT Scoring & Negative Marking Specification

## 1. Scoring Engine Pipeline

MCAT evaluation is conducted server-side by `AcademicCalculationService.calculate_mcat_score` using deterministic rules:

```
[ SUBMITTED RESPONSES ]
           ↓
For each question in Exam Blueprint:
  ├── Is question CANCELLED?
  │     Yes → Award full points to candidate (Fairness Protocol)
  │
  ├── Was question UNANSWERED?
  │     Yes → Zero points (no penalty)
  │
  ├── Did candidate answer CORRECTLY?
  │     Yes → + points (default 1.0)
  │
  └── Did candidate answer INCORRECTLY?
        ├── Negative marking enabled?
        │     Yes → - (points * negative_penalty) [Default 0.25]
        │     No  → Zero points
```

---

## 2. Mathematical Formalism

$$\text{Raw Score} = \max\left(0, \, \sum_{q \in \text{Correct}} P_q + \sum_{q \in \text{Cancelled}} P_q - \sum_{q \in \text{Incorrect}} (\lambda \times P_q)\right)$$

Where:
- $P_q$ = Point value for question $q$ (typically $1.0$).
- $\lambda$ = Negative marking penalty factor (typically $0.25$).
- Negative raw scores are clamped to `0.0`.

$$\text{Percentage} = \operatorname{round}\left(\frac{\text{Raw Score}}{\text{Maximum Possible Score}} \times 100.0, \, 2\right)$$

- Candidate passes if $\text{Percentage} \ge 40.0\%$.
