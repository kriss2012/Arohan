# ISDP Platform Security Specification

**Standard**: Institutional Grade Cybersecurity Architecture  
**Scope**: Authentication, Authorization, RBAC, Data Protection, Audit

---

## 1. Authentication & Session Architecture

- **Password Hashing**: Argon2id / bcrypt with work factor 12. Plaintext passwords are never logged or stored.
- **JWT Authentication**:
  - `access_token`: Short-lived (15 minutes), signed with HMAC-SHA256 / Ed25519.
  - `refresh_token`: Rotating single-use token (7 days) stored securely in HTTP-only cookies or encrypted desktop local storage.
  - Automatic token revocation on logout or credential change.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Route Group | SUPER_ADMIN | INSTITUTE_ADMIN | HOD | FACULTY | EXAM_CONTROLLER | PLACEMENT_OFFICER | MENTOR | STUDENT |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `/admin/*` | **RW** | **RW** | - | - | - | - | - | - |
| `/curriculum/*` | **RW** | **RW** | **RW** | **RW** | - | - | R | R |
| `/mcat/exams` | **RW** | R | R | R | **RW** | R | R | R (Enrolled) |
| `/mcat/attempts/start` | - | - | - | - | - | - | - | **W** |
| `/exam-controller/*` | **RW** | - | R | - | **RW** | - | - | - |
| `/arohan/*` | R | R | R | R | - | R | R | **RW** (Self) |
| `/faculty/interventions` | - | - | R | **RW** | - | - | R | - |
| `/placement/*` | **RW** | R | R | - | - | **RW** | - | R (Self) |

*Key: RW = Read/Write, R = Read-Only, W = Write-Only, - = Access Denied (403 Forbidden).*

---

## 3. Threat Mitigation Controls

1. **Broken Object Level Authorization (BOLA / IDOR)**: Service methods explicitly verify that `attempt.student_id == current_user.id` or that the user holds an administrative role with matching `department_id`.
2. **SQL Injection**: Strictly prevented using SQLAlchemy parameterized queries and ORM mappings.
3. **Cross-Site Scripting (XSS)**: All student-rendered text is sanitized with DOMPurify, and Content Security Policy (CSP) headers are strictly enforced.
4. **Audit Logging**: All security-critical events (login, role assignment, blueprint publish, exam attempt submission, integrity alert) generate an immutable entry in `audit_logs`.
