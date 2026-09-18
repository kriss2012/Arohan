# AROHAN AI Safety & Institutional Security Architecture

## 1. Core Principle: AI is Not a Security Boundary

The AROHAN AI engine provides adaptive recommendations, skill gap summaries, and remedial study guidance. However, **AI is explicitly treated as an untrusted processing component**:
- **Rule 1: AI Never Modifies Official Academic Records**: AI cannot change marks, alter grades, publish results, change roles, or delete records. Official modifications require deterministic workflows executed by authorized faculty or administrators.
- **Rule 2: Authorization Precedes AI Context Assembly**: An LLM is never asked whether a student is allowed to see data. Deterministic application code filters data before the model ever sees it.
- **Rule 3: Deterministic Calculations**: Percentages, grades, GPAs, and MCAT scores are never computed by an LLM.

---

## 2. AROHAN AI Trust Boundary & Architecture

```
[ STUDENT / FACULTY USER ]
             │
             │ Authenticated API Request
             ▼
[ PERMISSION & DATA MINIMIZATION FILTER ]
             │
             │ Scoped Student Context Only
             ▼
[ SANITIZATION & PROMPT SHIELD ]
             │
             │ Sanitized Prompt Template
             ▼
[ AROHAN BAYESIAN & REASONING ENGINE ]
             │
             │ Explainable Recommendation
             ▼
[ EVIDENCE DRAWER & AUDIT LOG ]
```

---

## 3. Data Minimization & Context Scoping

When a student queries the AI engine for study recommendations:
- **Included Context**:
  - Authenticated student's Bayesian skill mastery probabilities (`P(L)`).
  - Number of correct/incorrect attempts for target skills.
  - Active curriculum subjects and remedial gaps.
- **Strictly Excluded Context**:
  - Peer student records, identities, or marks.
  - Institutional administrative logs, system credentials, or database connection strings.
  - Unrelated departmental syllabi or exam answer keys.

---

## 4. Explainability & Grounding Standards

1. **Evidence Reference Requirement**: Every recommendation must cite underlying Bayesian Knowledge Tracing (BKT) metrics (e.g. `Mastery: 48%, Gap Score: 0.62`).
2. **Transparent Confidence Levels**: Rather than fabricated probability claims, outputs use documented evidence tiers:
   - `HIGH EVIDENCE` (> 5 verified assessment attempts)
   - `MODERATE EVIDENCE` (2–4 attempts)
   - `INSUFFICIENT EVIDENCE` (< 2 attempts; recommendation withheld until sufficient practice is completed).
