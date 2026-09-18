# AROHAN AI Continuous Diagnostic Data Flow

## 1. Closed-Loop Adaptive Learning Architecture
Every student academic touchpoint feeds into a closed-loop personalized diagnostic pipeline:

```
STUDENT ACTION (MCAT response, assignment submission, coding task)
                        ↓
             EVIDENCE LOGGED (skill_evidence)
                        ↓
       BAYESIAN KNOWLEDGE TRACING (BKT) UPDATE:
         P(L_t | Correct) or P(L_t | Incorrect)
                        ↓
            STUDENT PROGRESS RECALCULATION
                        ↓
            SKILL GAP DETECTION (< 0.70 mastery)
                        ↓
         PREREQUISITE DEPENDENCY GRAPH TRAVERSAL
                        ↓
           AROHAN RECOMMENDATION GENERATION
                        ↓
        RECOMMENDATION STORED IN recommendations TABLE
                        ↓
              STUDENT IN-APP NOTIFICATION
                        ↓
      STUDENT COMPLETES TARGETED INTERVENTION / DRILL
                        ↓
        NEW EVIDENCE RECORDED -> MASTERY INCREASES
```

## 2. Recommendation Traceability & Evidence Drawer
Every recommendation records:
- `student_id`: Target student.
- `skill_id`: Targeted competency.
- `recommendation_type`: REMEDIATION, DRILL, ADVANCED_CHALLENGE.
- `reason`: Pedagogical justification.
- `evidence_ids`: JSON array linking the specific assessment questions, assignments, or MCAT items that triggered the recommendation.
- This ensures 100% auditable, transparent AI guidance that faculty, mentors, and students can inspect.
