# Student Progress Calculation & Multi-Component Weighting Specification

## 1. Weighted Progress Model

Overall student progress is deterministically synthesized from six verified academic components defined in `progress_weight_configs`:

$$\text{Overall Progress} = \sum_{c \in \text{Components}} \left(\frac{W_c}{\sum W} \times \operatorname{clamp}(S_c, 0, 100)\right)$$

### Institutional Weight Distribution (Default Config):

| Academic Component | Configurable Weight | Description |
| :--- | :---: | :--- |
| **Assignments** ($S_{\text{assign}}$) | **20%** ($0.20$) | Average score across graded homework and problem sets. |
| **Assessments** ($S_{\text{assess}}$) | **25%** ($0.25$) | Mid-term examinations and laboratory practicals. |
| **MCAT Exams** ($S_{\text{mcat}}$) | **15%** ($0.15$) | Multiple-choice adaptive skill tests and mock evaluations. |
| **Coding Exercises** ($S_{\text{code}}$) | **15%** ($0.15$) | Automated sandbox unit test pass rates. |
| **Projects** ($S_{\text{proj}}$) | **15%** ($0.15$) | Capstone milestone evaluations and faculty viva scores. |
| **Learning Activities** ($S_{\text{act}}$) | **10%** ($0.10$) | Syllabus unit reading, resource views, practice engagement. |
| **Total** | **100%** ($1.00$) | |

---

## 2. Explainability & Component Breakdown

Progress metrics are never presented as unexplained magic numbers. Whenever `StudentProgress.overall_progress` is displayed:
- The UI exposes the exact individual contribution of each component:
  $$\text{Contribution}_c = W_c \times S_c$$
- Students and academic advisors can trace the exact calculation back to individual graded assignments and completed MCAT attempts.

---

## 3. Reconciliation & Anti-Drift Protocol

The system provides an automated reconciliation routine (`AcademicCalculationService.reconcile_student_progress`):
- Recomputes the expected progress from current component scores.
- Compares against stored `StudentProgress.overall_progress`.
- If the difference exceeds `0.05%`, a `DATA_INTEGRITY_ALERT` is logged without silent data overwriting.
