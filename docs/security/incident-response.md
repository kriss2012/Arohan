# Institutional Incident Response Plan

## 1. Incident Response Lifecycle

The Incident Response Plan governs the detection, containment, eradication, and recovery from potential security breaches or data integrity alerts in the campus environment:

```
[ DETECT & IDENTIFY ]
Automated integrity alerts / Audit mismatch / Repeated lockout spikes
          ↓
[ CONTAINMENT ]
Immediate session revocation / Account deactivation / Network quarantine
          ↓
[ EVIDENCE PRESERVATION ]
Immutable snapshot of SQLite WAL / Physical file hashes / Memory dump
          ↓
[ ANALYSIS & ROOT CAUSE ]
Cryptographic audit chain scan / Access log tracing / Git diff inspection
          ↓
[ ERADICATION ]
Lifting unauthorized access / Patching vulnerability / Rotating compromised secrets
          ↓
[ RECOVERY & VERIFICATION ]
Restoring verified backup / Running automated integrity scanners
          ↓
[ POST-INCIDENT REVIEW ]
Documenting timeline, lessons learned, and institutional reporting
```

---

## 2. Incident Severity Classification

| Severity Level | Definition | Examples | Response Target |
| :--- | :--- | :--- | :--- |
| **P0 - CRITICAL** | Active compromise of database, result manipulation, or secret exposure. | Direct SQL tampering, leaked master JWT secret, unverified result edits. | Immediate action (< 1 hour); emergency incident team assembled. |
| **P1 - HIGH** | Privilege escalation attempt, file upload bypass, or audit chain break. | Student accessing `/admin/users`, executable uploaded, audit hash mismatch. | Containment within 4 hours. |
| **P2 - MEDIUM** | Repeated brute-force lockouts or single-user suspicious session pattern. | 50+ failed logins on faculty accounts; cross-lab token reuse. | Investigation within 24 hours. |
| **P3 - LOW** | Minor hardening warnings or single-time validation rejection. | Disguised extension upload blocked; invalid query parameters. | Reviewed in weekly security audits. |

---

## 3. Evidence Preservation Protocol

1. **Do Not Truncate or Delete Logs**: Never restart SQLite or delete `audit_logs` during an ongoing investigation.
2. **Snapshot SQLite File**: Create an immediate copy of `isdp_campus.db`, `isdp_campus.db-wal`, and `isdp_campus.db-shm` to a secure external media.
3. **Compute SHA-256 Hashes**: Hash all preserved artifacts immediately to prove chain of custody.
