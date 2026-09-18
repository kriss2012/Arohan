# Disaster Recovery & Restoration Verification Protocol

## 1. Disaster Scenarios & Recovery Objectives

| Disaster Scenario | Recovery Objective | Target Metrics |
| :--- | :--- | :--- |
| **Server Hardware Failure** | Provision replacement server; restore database and assets from NAS or offline drive. | **RTO** (Recovery Time Objective): < 2 hours<br>**RPO** (Recovery Point Objective): < 24 hours |
| **Ransomware on Host** | Wipe host server; reinstall OS; restore from verified offline air-gapped backup. | **RTO**: < 4 hours<br>**RPO**: < 24 hours |
| **Accidental Database Deletion** | Rollback to most recent automated daily snapshot. | **RTO**: < 30 minutes<br>**RPO**: < 12 hours |

---

## 2. Periodic Restoration Testing Routine

*Critical Institutional Rule: A backup is not considered reliable until its restoration has been successfully proven in an isolated test environment.*

The disaster recovery protocol requires monthly restoration exercises:

```
[ BACKUP ZIP BUNDLE ]
        ↓
[ STEP 1: Checksum Verification ]
Validate bundle SHA-256 against manifest.json.
        ↓
[ STEP 2: Extract to Isolated Test Environment ]
Restore SQLite snapshot and files directory to sandbox environment.
        ↓
[ STEP 3: Run Database Migrations & Health Checks ]
Run schema migrations; verify SQLite integrity check (`PRAGMA integrity_check`).
        ↓
[ STEP 4: Entity Verification ]
Verify user count, assignment count, result records, and submission files match manifest.
        ↓
[ STEP 5: Audit Log Chain Verification ]
Execute `AuditService.verify_audit_chain` on restored database.
        ↓
[ STEP 6: Mark Backup Verified ]
Update backup status in administrative ledger: `STATUS = VERIFIED_RESTORED`.
```

---

## 3. Automated Emergency Recovery Checklist

1. Halt active FastAPI backend process to avoid concurrent file locking.
2. Archive the current corrupt database directory to `./quarantine/` for forensics.
3. Unpack the verified backup snapshot to `isdp_campus.db`.
4. Restore `./local_storage/` from `files_archive/`.
5. Run `python -m backend.app.db.migrate_security_schema`.
6. Start backend process and verify `/api/v1/security/dashboard` reports `OPTIMAL`.
