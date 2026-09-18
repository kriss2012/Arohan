# Data Integrity & Automated Consistency Scanner Specification

## 1. Automated Integrity Scanners

The platform implements continuous data integrity verification via `backend.app.services.data_integrity_service.DataIntegrityService`:

### A. Physical File Storage Integrity Scanner
- **Function**: `scan_file_storage_integrity(db)`
- **Mechanism**:
  1. Traverses all records in `files` table.
  2. Resolves path against `STORAGE_ROOT`.
  3. Verifies physical file exists on disk.
  4. Streams binary contents and recalculates SHA-256 hash.
  5. Compares computed hash against `checksum_sha256`.
  6. Flags missing or altered files as critical integrity events without destructive auto-deletion.

### B. Relational & Constraint Consistency Scanner
- **Function**: `scan_database_consistency(db)`
- **Checks Executed**:
  1. Users with no assigned roles.
  2. Out-of-bounds result marks ($< 0$ or $> \text{max\_marks}$).
  3. Out-of-bounds percentages ($< 0.0\%$ or $> 100.0\%$).
  4. Orphan assignment submissions pointing to missing assignments.
  5. Dangling active sessions on deactivated or suspended user accounts.

### C. Cryptographic Audit Trail Verification
- **Function**: `AuditService.verify_audit_chain(db)`
- **Mechanism**: Validates the cryptographic SHA-256 hash links across all historical audit entries. Flags any record modified, removed, or inserted.
