# ISDP + AROHAN AI System: Current State & Repository Audit

**Date of Inspection**: 2026-09-18  
**Repository**: `c:\Users\IMRD\Documents\GitHub\Arohan`  
**Inspected By**: Senior Engineering Team (Autonomous Execution)

---

## 1. Executive Summary

A comprehensive repository and environment audit was conducted prior to code initialization. The repository was an empty root directory initialized for the **Institute Student Development Platform (ISDP)**. All development prerequisites are active on the host machine.

---

## 2. Environment & Tooling Audit

| Tool / Runtime | Version Detected | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Python** | 3.14.7 | Active | Modern asynchronous runtime available |
| **Node.js** | v24.19.0 | Active | Modern ESM & Vite compatible |
| **NPM** | 11.17.0 | Active | Package management ready |
| **Rust / Cargo** | 1.98.1 | Active | Tauri desktop native compilation ready |
| **Git** | 2.55.0.windows.5 | Active | Version control ready |
| **Database Engines** | SQLite 3.50.4 (Internal) / PostgreSQL Target | Active | SQLite for local offline test & dev; Postgres schema for production |
| **Docker** | Not in system PATH | Optional | Handled via self-contained Python & Node services |

---

## 3. Existing Architecture & Components

- **Prior Codebase**: Freshly initialized project. No legacy technical debt or deprecated packages to carry forward.
- **Institutional Reference**: RC Patel Educational Trust's Institute of Management Research and Development (IMRD), Shirpur.
  - Institutional design cues: Formal academic hierarchy, navy blue (`#0f2b5c`), royal academic blue (`#1d4ed8`), clean slate white backgrounds, rigorous academic audit trails.
- **Architectural Paradigms**:
  1. **Modular Monolith**: FastAPI backend with cleanly separated domain modules (`curriculum`, `mcat`, `evidence`, `arohan_ai`, `exam_controller`, `auth`).
  2. **Dual-Tier Persistence**: SQLAlchemy with async engine supporting both PostgreSQL (with pgvector in production) and SQLite (for zero-dependency local verification and desktop offline encrypted store).
  3. **Desktop-First Secure LMS**: React + TypeScript + Vite frontend wrapped with Tauri for native OS-level kiosk and exam lockdown capabilities.
  4. **Evidence-Driven AI**: Bayesian Knowledge Tracing (BKT) and Item Response Theory (IRT) calibrated before statistical recommendation output.

---

## 4. Technical Debt & Risk Assessment

1. **Risk: AI Hallucination & Score Fabrication**
   - *Mitigation*: Strictly enforce the rule that AI never invents student scores, attendance, or mastery. If data is lacking, status returns `INSUFFICIENT_EVIDENCE`.
2. **Risk: False Cheating Accusations**
   - *Mitigation*: Renamed all monitoring alerts to **Integrity Signals** (Low, Medium, High). No automated disciplinary actions; all signals feed into the Exam Controller audit log for human review.
3. **Risk: Exam Desynchronization & Clock Tampering**
   - *Mitigation*: Client maintains a signed server-time delta (`client_server_offset`). All exam timers and expiration events are server-authoritative.
4. **Risk: Local Database Lockup**
   - *Mitigation*: High-concurrency WAL mode enabled for SQLite during local runs, connection pooling configured for PostgreSQL.

---

## 5. Next Immediate Steps

1. Produce complete architectural specifications across the 12 `/docs/` reference guides.
2. Initialize backend modular monolith with FastAPI, SQLAlchemy models, Pydantic schemas, and JWT RBAC for 8 distinct roles.
3. Initialize the React + TypeScript frontend with institutional styling and the Tauri desktop bridge.
4. Implement the seed data engine populated with realistic academic departments (BCA, MCA), course syllabus, and MCAT diagnostic aptitude banks.
