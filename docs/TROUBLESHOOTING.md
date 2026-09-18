# ISDP Platform: Troubleshooting & Recovery Runbook

---

## 1. MCAT Exam Session Issues

### Symptom: Candidate network disconnected during high-stakes exam.
- **Root Cause**: Transient campus Wi-Fi or laboratory Ethernet interruption.
- **Resolution**:
  1. Desktop client continues in `OFFLINE_ACTIVE` mode with local encryption.
  2. The local timer relies on the signed `client_server_offset` token established at start.
  3. When connection re-establishes, the client sends queued responses using idempotency keys.
  4. If disconnection exceeds policy threshold, session transitions to `INTERRUPTED`. Student can resume with Exam Controller authorization.

### Symptom: Candidate accidentally triggered `FOCUS_LOST` signal.
- **Root Cause**: OS background notification, antivirus popup, or accidental mouse movement outside window.
- **Resolution**:
  1. The platform records this as a neutral `Integrity Signal` (Severity: LOW).
  2. The exam is NOT terminated.
  3. Controller console logs the event with exact duration. No automatic punishment is applied.

---

## 2. AROHAN AI & Skill Diagnostics Issues

### Symptom: AI returns `INSUFFICIENT_EVIDENCE` for a student skill.
- **Root Cause**: Fewer than 3 valid assessment observations have been recorded for this specific skill.
- **Resolution**:
  - This is expected system behavior enforcing the zero-fabrication ethical rule.
  - Advise the student to take a diagnostic MCAT section or complete a relevant curriculum quiz to establish a baseline.

---

## 3. Database Connection Issues

### Symptom: `database is locked` during concurrent SQLite writes.
- **Root Cause**: High-concurrency operations under standard SQLite rollback journal.
- **Resolution**: Ensure WAL (Write-Ahead Logging) mode and busy timeouts are configured in database initialization engine: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`.
