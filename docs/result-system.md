# Result System & Security Specification

## 1. Academic Results Architecture
The `results` table is the institutional source of truth for formal academic evaluations:
- `student_id`: Target student UUID.
- `subject_id`: Associated academic course.
- `assessment_id` / `assignment_id`: Originating assessment or assignment.
- `marks`: Numeric score obtained.
- `max_marks`: Total potential score.
- `percentage`: Computed score percentage `(marks / max_marks) * 100`.
- `grade`: Standardized letter grade (O, A+, A, B, C, D, F).
- `grade_point`: Grade point index on a 10.0 scale.
- `result_status`: `PASSED` or `FAILED`.
- `published`: Boolean flag controlling student visibility.
- `published_at`: Timestamp when the result was made public.
- `published_by`: Faculty or Exam Controller UUID who authorized the publication.

## 2. Result Modification Auditing
- Results cannot be modified without creating an immutable entry in `audit_logs`.
- The audit log stores `user_id`, `action = 'MARKS_CHANGED'`, `old_value`, `new_value`, and the request IP address.
- Historical transcripts remain preserved even if a student retakes an examination or completes an improvement assignment.
