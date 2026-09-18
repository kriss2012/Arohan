# Institutional Database Security Specification

## 1. Local-First Database Architecture

The ISDP database engine runs entirely on premise under institutional control.
- **Engine**: SQLite in Write-Ahead Logging (WAL) mode (`isdp_campus.db`).
- **Zero Cloud Exposure**: The database does not listen on any public network interface. Direct socket connections from client machines are completely blocked.
- **Access Boundary**: Only the local FastAPI backend runtime process has filesystem access to `isdp_campus.db`.

```
[ STUDENT / FACULTY WORKSTATIONS ]
             │
             │ HTTPS (API Requests Only)
             ▼
[ LOCAL BACKEND (FastAPI / SQLAlchemy ORM) ]
             │
             │ Local File / UNIX / Named Pipe
             ▼
[ SQLite DATABASE (WAL Mode - Local Disk) ]
```

---

## 2. SQL Injection Defense

1. **Strict Parameterized Queries**: All database interactions use SQLAlchemy ORM queries with parameterized bind values.
2. **Zero Raw Concatenation**: Dynamic string concatenation (`f"SELECT ... WHERE email = '{email}'"`) is strictly prohibited.
3. **ORM Escaping**: Inbound filters, pagination limits, and search strings are safely escaped by the database dialect.

---

## 3. Database Constraints & Schema Hardening

1. **Foreign Key Enforcement**: Foreign key constraints are enforced (`PRAGMA foreign_keys = ON;`) to prevent orphan records.
2. **CHECK Constraints**:
   - `percentage >= 0.0 AND percentage <= 100.0`
   - `marks >= 0.0 AND marks <= max_marks`
3. **Unique Constraints**: Email addresses, student enrollment numbers, and stored file hashes are strictly unique.
4. **Optimistic Concurrency Control**: High-stakes academic entities maintain a `version` column (e.g. `results.version`). Modifications verify the expected version before committing, rejecting conflicting concurrent edits.

---

## 4. Encryption & Protection at Rest

1. **Disk-Level Volume Encryption**: The host campus server employs BitLocker (Windows) or LUKS (Linux) full-volume encryption for the storage drive housing `isdp_campus.db`.
2. **Protected Backup Bundles**: Automated backups encrypt the SQLite database snapshot and stored assets into an encrypted ZIP bundle.
3. **Credential Isolation**: Database paths and secrets reside strictly in environment variables and are never packaged into client bundles.
