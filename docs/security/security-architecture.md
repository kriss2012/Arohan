# Institutional Security Architecture Specification

## Institute Student Development Platform (ISDP) - Local-First Security Architecture

### 1. Architectural Philosophy: Zero-Trust & Defense-in-Depth

The Institute Student Development Platform (ISDP) operates under a strict **Zero-Trust Institutional Security Architecture**. In a local campus environment, perimeter network trust is considered an anti-pattern. No request is trusted merely because it originates from within the institute's physical LAN, from localhost, from a faculty terminal, or from the desktop client.

Every sensitive academic and administrative request traverses an eight-layer security pipeline before business execution:

```
[ CLIENT SURFACE ]
Desktop Client (Tauri / Browser Webview)
        ↓
[ TRANSPORT LAYER ]
Local Intranet TLS (HTTPS / WSS with Institute CA)
        ↓
[ PERIMETER & RATE LIMITING ]
Strict CORS allowlist + Progressive Throttling + Request Size Bounds
        ↓
[ IDENTITY & SESSION VALIDATION ]
JWT Signature & Expiration + Cryptographic Revocation Check (user_sessions)
        ↓
[ ROLE-BASED ACCESS CONTROL (RBAC) ]
Backend-Enforced Roles (SUPER_ADMIN, INSTITUTE_ADMIN, HOD, FACULTY, EXAM_CONTROLLER, STUDENT)
        ↓
[ FINE-GRAINED RESOURCE AUTHORIZATION & SCOPING ]
Departmental Isolation + Subject Scoping + Ownership Validation (student_id / faculty_id)
        ↓
[ BUSINESS LOGIC & DETERMINISTIC VALIDATION ]
Pydantic Schemas + Boundary Constraints + State Machine Checks
        ↓
[ DATABASE CONSTRAINTS & ATOMIC TRANSACTIONS ]
ACID Transactions + Foreign Keys + CHECK Constraints + Versioning
        ↓
[ APPEND-ONLY CRYPTOGRAPHIC AUDIT LOGGING ]
SHA-256 Hash Chained Audit Trail (Tamper-Evident)
```

---

### 2. Multi-Layer Protection Matrix

| Architecture Layer | Threats Mitigated | Controls Implemented |
| :--- | :--- | :--- |
| **Desktop Client** | Reverse engineering, memory tampering, token theft | Minimized Tauri capabilities; no hardcoded master secrets; zero trust in frontend state; authoritative server clock. |
| **Transport Layer** | LAN eavesdropping, ARP spoofing, session sniffing | Local TLS termination; encrypted cookies/headers; server-authoritative timestamps (`X-Server-Time-UTC`). |
| **Authentication** | Brute force, credential stuffing, unauthorized signup | No public self-registration; Admin allowlist (`authorized_users`); 6-digit cryptographic OTP; mandatory 12+ character password setup; 15-min lockout after 5 failed attempts. |
| **Authorization** | IDOR, BOLA, horizontal/vertical privilege escalation | Deny-by-default; session-derived caller identity; departmental and student ownership checks on all endpoints. |
| **API & Business Logic** | Mass assignment, formula injection, path traversal | Pydantic strict schemas; formula character stripping (`=`, `+`, `-`, `@`); sanitized file basename hashing. |
| **Database & Storage** | Data corruption, silent tampering, malicious uploads | Local SQLite WAL mode with atomic transactions; magic-byte binary inspection (`%PDF`, `PK\x03\x04`, `PNG`, `JPEG`); non-colliding UUID filenames; SHA-256 checksum tracking. |
| **AROHAN AI / RAG** | Data leakage, prompt injection, hallucinations | Context minimization; permission-checked retrieval; strict instruction/content segregation; AI strictly barred from altering official records. |
| **Audit & Governance** | Repudiation, unauthorized admin actions, log truncation | Append-only audit trail with SHA-256 cryptographic hash chaining (`record_hash = sha256(prev_hash + canonical_event)`); automated chain tamper detection. |

---

### 3. Trust Boundaries

1. **Client Boundary**: Desktop clients are considered untrusted execution environments. Client-side timers, scores, roles, and IDs are never authoritative.
2. **Local LAN Boundary**: Physical network segments are treated as public. All inter-process communication relies on authenticated tokens.
3. **Database Boundary**: Database communication is strictly restricted to the local backend process using least-privilege credentials.
4. **AI & Model Boundary**: The AROHAN AI service operates behind an authorization gateway. It receives only pre-filtered, scoped student data and cannot access cross-department records or administrative credentials.
