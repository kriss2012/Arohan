# ISDP: Automated Testing & Verification Strategy

**Quality Standard**: Continuous Phase-Gate Verification  

---

## 1. Test Architecture Overview

```
+-------------------------------------------------------------+
| End-to-End User Journey Tests (Browser Subagent / Playwright)|
+-------------------------------------------------------------+
| Integration Tests (API + DB + BKT Pipeline + FSM Lifecycle) |
+-------------------------------------------------------------+
| Unit Tests (BKT Formulas, IRT Math, Password Hash, Schemas) |
+-------------------------------------------------------------+
```

---

## 2. Core Test Suites

### 2.1 Bayesian Knowledge Tracing Math Suite (`test_bkt_service.py`)
- Verify initial prior $P(L_0) = 0.10$.
- Test consecutive correct answers: verify $P(L_t)$ increases monotonically towards $1.0$.
- Test slip & guess resilience: ensure single incorrect answer does not zero out a previously learned skill.
- Test skill gap calculation and `INSUFFICIENT_EVIDENCE` guard when observations $< 3$.

### 2.2 MCAT 11-State Lifecycle Suite (`test_mcat_fsm.py`)
- Verify valid path: `CREATED -> AUTHORIZED -> STARTED -> SUBMITTED -> AUTO_EVALUATED -> FINALIZED`.
- Verify invalid transitions are rejected with HTTP 400 (e.g. `STARTED -> FINALIZED` directly).
- Verify pause and resume preserving time-remaining with server clock delta.
- Verify automatic scoring: 100% accurate calculation of domain breakdown (Quant, Logical, Verbal, DI).

### 2.5 Authorized Email Allowlist & Lockout Suite (`test_authorized_auth.py`)
- Verify arbitrary registration is rejected (`HTTP 403`).
- Verify authorized user account activation with activation code.
- Verify brute-force lockout after 5 consecutive failed attempts (`HTTP 403`).
- Verify administrator manual account unlock.

### 2.6 Local Storage & Security Suite (`test_local_storage.py`)
- Verify safe file upload with SHA-256 calculation.
- Verify magic bytes inspection blocks disguised `.exe` / `.dll` files (`HTTP 400`).
- Verify file download with `X-Checksum-SHA256` integrity header.

### 2.7 Academic Lifecycle End-to-End Suite (`test_assignment_progress_e2e.py`)
- Full round-trip: Faculty assignment creation -> Student file submission -> Faculty grading -> Result record -> BKT skill evidence -> Student progress recalculation -> Anti-IDOR check.

### 2.8 Database Health & Backup Suite (`test_backup_restore.py`)
- Verify `/admin/database/health` reports `OPTIMAL` status.
- Verify local storage statistics calculation.
- Verify creation of verified ZIP backup bundle with SHA-256 manifest.

---

## 3. Test Execution & Verification Results
```bash
python -m pytest backend/tests -v
============================= 18 passed in 10.05s =============================
```
- Total Suites: 18 passed / 0 failed (100% Pass Rate).
- Zero external internet dependencies required during execution.
