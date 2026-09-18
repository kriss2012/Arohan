# Student Progress Engine Specification

## 1. Configurable Weight Matrix
Progress is not hardcoded; it is governed by the `progress_weight_configs` table configured per institution:
- **Assignment Weight**: 20% (0.20)
- **Assessment Weight**: 25% (0.25)
- **MCAT / Aptitude Weight**: 15% (0.15)
- **Coding Practice Weight**: 15% (0.15)
- **Projects Weight**: 15% (0.15)
- **Learning Activity Weight**: 10% (0.10)
- **Total Weight Constraint**: $\sum \text{weights} = 1.00$ (100%).

## 2. Event-Driven Recalculation Loop
Whenever any student milestone occurs:
- `ASSIGNMENT_EVALUATED`
- `ASSESSMENT_COMPLETED`
- `MCAT_COMPLETED`
- `RESOURCE_COMPLETED`

The backend `ProgressService.recalculate_student_progress(student_id, subject_id)` executes:
1. Calculates `assignment_score` from all evaluated submissions.
2. Calculates `assessment_score` from all verified tests.
3. Computes the weighted overall progress percentage:
   $$\text{Overall Progress} = \sum (\text{Component Score} \times \text{Weight})$$
4. Updates `student_progress` table with `overall_progress`, `completion_percentage`, and `last_activity_at`.
5. Updates the longitudinal student model feeding the AROHAN AI advisory pipeline.
