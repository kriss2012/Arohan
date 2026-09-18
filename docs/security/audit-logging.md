# Cryptographic Audit Logging & Tamper Detection Specification

## 1. Objectives of Institutional Audit Logging

The audit system provides tamper-evident accountability and non-repudiation for high-stakes institutional operations:
- Identifying which identity performed an action.
- Recording exactly when and on what resource the action took place.
- Guaranteeing that log entries cannot be modified, reordered, or deleted without immediate mathematical detection.

---

## 2. Cryptographic Hash Chaining Design

Audit records in the `audit_logs` table form a sequential, append-only cryptographic hash chain modeled on blockchain/Merkle structures:

```
[ GENESIS HASH ] (64 zeros)
        │
        ▼
[ RECORD 0 ]
  previous_hash: 0000000000000000000000000000000000000000000000000000000000000000
  canonical_data: prev_hash | user_id | action | entity_type | entity_id | details | timestamp
  record_hash: SHA-256(canonical_data) ──┐
                                          │
        ┌─────────────────────────────────┘
        ▼
[ RECORD 1 ]
  previous_hash: <RECORD 0 record_hash>
  canonical_data: prev_hash | user_id | action | entity_type | entity_id | details | timestamp
  record_hash: SHA-256(canonical_data) ──┐
                                          │
        ┌─────────────────────────────────┘
        ▼
[ RECORD 2 ]
  previous_hash: <RECORD 1 record_hash>
  ...
```

---

## 3. Mandatory Audit Events & Severity

| Event Name | Security Severity | Audited Details |
| :--- | :--- | :--- |
| `USER_AUTHORIZED` | INFO | Admin UUID, authorized email, intended role. |
| `LOGIN_SUCCESS` | INFO | User UUID, IP address, user agent. |
| `LOGIN_FAILED` | LOW | Attempted email, IP address, failure count. |
| `ACCOUNT_LOCKED` | HIGH | User UUID, lockout timestamp (after 5 failures). |
| `PASSWORD_SETUP` | INFO | User UUID, setup timestamp. |
| `PASSWORD_RESET` | MEDIUM | User UUID, session revocation count. |
| `USER_DEACTIVATED` | HIGH | Target user UUID, admin UUID, sessions revoked. |
| `RESULT_PUBLISHED` | MEDIUM | Student UUID, subject ID, marks, grade. |
| `RESULT_MODIFIED` | CRITICAL | Student UUID, old marks, new marks, change reason. |
| `FILE_INTEGRITY_ALERT` | CRITICAL | Path, expected checksum, actual computed checksum. |
| `DATA_INTEGRITY_ALERT` | HIGH | Student UUID, expected progress, stored progress. |
| `TAMPER_DETECTED` | CRITICAL | Record ID, corrupt index, expected vs actual hash. |

*Redaction Policy: Passwords, plaintext OTPs, raw reset tokens, and decryption keys are NEVER written to logs.*

---

## 4. Automated Chain Verification Scanner

The service `AuditService.verify_audit_chain` runs periodically or on administrative demand:
1. Loads all records ordered by `timestamp ASC, id ASC`.
2. Verifies that `current_record.previous_hash == preceding_record.record_hash`.
3. Recomputes `SHA-256(canonical_data)` for each record and validates that `recomputed_hash == current_record.record_hash`.
4. If an attacker modifies an entry directly in SQLite, the recomputed hash immediately mismatches, returning `status: "TAMPER_DETECTED"` and identifying the exact record corrupted.
