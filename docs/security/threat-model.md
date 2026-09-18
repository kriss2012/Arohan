# Institutional Threat Model (STRIDE Methodology)

## System Overview & Asset Inventory

The Institute Student Development Platform (ISDP) manages high-value institutional assets in a local-first environment:
- **Identity Assets**: Passwords, OTP hashes, session tokens, user profile metadata.
- **Academic Assets**: Official marks, GPA, question banks, MCAT exams, answer keys, evaluations, assignment submissions.
- **System Assets**: SQLite database file (`isdp_campus.db`), local file storage repository (`./local_storage/`), cryptographic audit logs, automated backup bundles (`./backups/`).

---

## 1. Threat Actors & Capabilities

| Threat Actor | Motivation / Objective | Potential Vectors |
| :--- | :--- | :--- |
| **Untrusted Outsider (LAN)** | Network scanning, brute force, intercepting plaintext data | LAN packet capture, ARP poisoning, accessing unauthenticated endpoints. |
| **Compromised Student** | Inflating marks, viewing upcoming exams, stealing peers' submissions | Modifying client-side code, IDOR parameter tampering, session hijacking. |
| **Malicious Insider / Rogue Staff** | Fabricating credentials, altering official results, deleting logs | Direct database tampering, privilege abuse, unauthorized data export. |
| **Compromised Endpoint / Malware** | Ransomware encryption, credential extraction, keylogging | Memory scraping, disk manipulation, file overwriting. |

---

## 2. STRIDE Threat Analysis & Applied Mitigations

### A. Spoofing Identity
- **Threat**: An attacker attempts to impersonate another student or administrator using stolen credentials, token forgery, or replay attacks.
- **Mitigation**:
  - Signed JWT access tokens with short TTL (15 minutes).
  - Cryptographically hashed rotating refresh tokens stored in `user_sessions`.
  - Immediate session revocation upon logout, password change, or administrative deactivation.
  - Zero public registration: Only administrator-authorized emails can activate accounts.

### B. Tampering with Data
- **Threat**: Modification of exam questions, marks, student evaluations, or file uploads on disk.
- **Mitigation**:
  - Result versioning (`result_versions`): Changes require an explicit reason and timestamp.
  - File integrity scanner: Verifies disk files against SHA-256 checksums in `files` table.
  - Append-only audit logs with SHA-256 hash chaining (`AuditService.verify_audit_chain`).
  - Strict database foreign key constraints and ACID transaction rollbacks on failure.

### C. Repudiation
- **Threat**: A faculty member denies modifying a grade; a student denies submitting an assignment or exam response.
- **Mitigation**:
  - Comprehensive, immutable audit trail logging actor UUID, role, action, IP address, timestamp, and entity references.
  - Cryptographic hash chaining ensures log entries cannot be retroactively modified or removed without immediate mathematical detection.

### D. Information Disclosure
- **Threat**: Exposure of exam answer keys, student progress, peer submissions, or internal database schemas.
- **Mitigation**:
  - IDOR defense: All self-service endpoints derive student identity from the authenticated session (`current_user.id`).
  - Answer keys are scored exclusively server-side and never sent to the client during an active exam attempt.
  - RAG data minimization: AI queries receive only the authenticated student's own competencies.

### E. Denial of Service (DoS)
- **Threat**: Flooding authentication endpoints, uploading massive files to exhaust disk space, runaway student coding loops.
- **Mitigation**:
  - Rate limiting on `/auth/login`, `/auth/check-email`, and `/auth/verify-code`.
  - 15-minute account lockout after 5 consecutive failed login attempts.
  - File upload restrictions: Maximum file size validation and magic bytes inspection.
  - Isolated coding execution with CPU, memory, and timeout caps.

### F. Elevation of Privilege
- **Threat**: A student modifies frontend state or API requests to call administrative endpoints or grant themselves elevated roles.
- **Mitigation**:
  - Server-authoritative RBAC enforced on every API route via `require_roles(...)`.
  - Frontend values (`role`, `is_admin`, `is_authorized`) are completely ignored by backend logic.
  - Admin endpoints require explicit re-validation and administrative permissions.
