# High-Stakes Examination & MCAT Assessment Security

## 1. Exam Integrity Objectives

Institutional examinations require strict confidentiality, authenticity, and non-repudiation:
- Students must only receive the questions assigned to their active attempt.
- The entire question bank must never be downloaded to student workstations.
- Answer keys must never be delivered to the client during an active test.
- Scoring must occur exclusively server-side.
- Attempt submissions must be atomic and idempotent.

---

## 2. Server-Side Question Delivery & Scoring

1. **Question Scoping**:
   - When a student initiates an attempt via `POST /api/v1/mcat/attempts/start`, the server selects questions based on the exam blueprint.
   - Question payload delivered to the client contains: `id`, `question_text`, `options` (`id`, `text`).
   - The field `is_correct` is completely stripped from the response payload.
2. **Server-Side Evaluation**:
   - Scoring happens in `AcademicCalculationService.calculate_mcat_score` upon submission.
   - Computes correct, incorrect, unanswered, and cancelled questions.
   - Applies institutional negative marking policies deterministically.
3. **Cancelled Question Protocol**:
   - If an examination committee cancels an erroneous question post-exam, the calculation engine automatically awards full credit to all candidates without recalculating or invalidating completed answers.

---

## 3. Idempotent Submission Pipeline

```
Student Clicks Submit
        ↓
Validate Active Session Token
        ↓
Validate Attempt State == 'IN_PROGRESS'
        ↓
Check Server-Authoritative Time <= attempt.expires_at
        ↓
Check Idempotency (Prevent Duplicate Double-Click Submissions)
        ↓
Lock Attempt (state = 'SUBMITTED')
        ↓
Score Responses Server-Side
        ↓
Record Skill Evidence to Bayesian Knowledge Tracing (BKT)
        ↓
Update Student Progress
        ↓
Append Cryptographic Audit Record
        ↓
Commit Transaction & Return Result
```

---

## 4. Live Integrity Telemetry

During active exams, the desktop client reports non-punitive integrity signals to the Exam Controller:
- Focus loss / window blur events.
- Fullscreen exit attempts.
- Clipboard copy/paste attempts.
- Abnormal response timing (< 1.5 seconds on complex questions).

*Institutional Safety Rule: Integrity events serve as alerts for human proctor review; the system never automatically fails or labels a student as a cheater based solely on automated telemetry.*
