# Local Backup and Disaster Recovery Specification

## 1. Unified Archive Model
A complete institutional backup requires both the database and physical files:
- **Database Dump**: Complete schema and records exported into `db_dump.sql` / database snapshot.
- **Physical Storage**: All files under `assignments/`, `submissions/`, `resources/`.
- **Integrity Manifest**: JSON file containing archive creation timestamp, total files, and cryptographic SHA-256 hash.
- **Packaging**: Compressed into `local_storage/backups/ISDP_BACKUP_<TIMESTAMP>.zip`.

## 2. Retention Policy
The local backup engine supports automatic retention pruning:
- **Daily Backups**: 7 retained.
- **Weekly Backups**: 4 retained.
- **Monthly Backups**: 12 retained.

## 3. Restore Pipeline & Safety Verification
Restoration is restricted to `SUPER_ADMIN`:
1. **Pre-Restore Snapshot**: The system takes an emergency snapshot of the current state before initiating restore.
2. **Manifest Verification**: The target backup's SHA-256 checksum and manifest are validated.
3. **Application Write Lock**: Active transactions and uploads are paused.
4. **Data Extraction & Migration Check**: Database and storage directories are safely restored.
5. **Post-Restore Health Check**: Connection pool, row counts, and storage availability are verified before reopening access.
