# Assignment Lifecycle & Workflow Specification

## 1. Complete Workflow
```
FACULTY LOGS IN
       ↓
SELECTS ASSIGNED SUBJECT
       ↓
CREATES ASSIGNMENT (Title, Instructions, Total Marks, Passing Marks, Due Date)
       ↓
UPLOADS ASSIGNMENT DOCUMENT (PDF/DOCX) -> Local Storage (SHA-256)
       ↓
ASSIGNMENT STATUS = 'PUBLISHED'
       ↓
ENROLLED STUDENTS RECEIVE NOTIFICATION & ASSIGNMENT IN DASHBOARD
       ↓
STUDENT DOWNLOADS BRIEF (X-Checksum-SHA256 verified)
       ↓
STUDENT SUBMITS SOLUTION FILE & TEXT (/api/v1/assignments/{id}/submit)
       ↓
SYSTEM RECORDS SUBMISSION (Checks if on-time or LATE, locks draft)
       ↓
FACULTY REVIEWS SUBMISSIONS LIST
       ↓
FACULTY DOWNLOADS SUBMISSION & EVALUATES:
       - Marks Obtained (Validated between 0 and total_marks)
       - Percentage & Letter Grade (A, B, C, D, F)
       - Feedback, Strengths, Areas for Improvement
       ↓
STATUS -> 'EVALUATED'
       ↓
OFFICIAL RESULT RECORD CREATED IN results TABLE
       ↓
SKILL EVIDENCE LOGGED (Bayesian Knowledge Tracing updated)
       ↓
STUDENT PROGRESS RECALCULATED
       ↓
AROHAN AI RE-ANALYZES GAPS & ISSUES RECOMMENDATIONS
```

## 2. Integrity Controls
- **Duplicate Submission Handling**: Student submissions increment `attempt_number` and preserve timestamp history.
- **Marks Range Validation**: Database CHECK constraints and backend validators ensure `0 <= marks <= total_marks`.
- **Soft Delete & Delete Protection**: Assignments with existing student submissions cannot be permanently deleted; they may only be archived to prevent academic record loss.
