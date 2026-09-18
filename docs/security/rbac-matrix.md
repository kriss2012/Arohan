# Complete Role-Based Access Control (RBAC) Matrix

## 1. System Roles

1. **SUPER_ADMIN**: Full system authority, security configuration, database backup/restore, audit review.
2. **INSTITUTE_ADMIN**: User management, authorization allowlist, faculty assignments, system health.
3. **HOD (Head of Department)**: Departmental curriculum management, faculty oversight, result verification.
4. **FACULTY**: Assignment creation, student submission evaluation, remedial intervention assignment.
5. **EXAM_CONTROLLER**: Question bank management, exam blueprint creation, live exam monitoring, result publication.
6. **PLACEMENT_OFFICER**: Placement readiness matrix, industry skill benchmark configuration.
7. **STUDENT**: Self-service learning, assignment submission, MCAT exam attempts, skill evidence review.

---

## 2. Resource Permissions Matrix

| Resource / Action | STUDENT | FACULTY | HOD | EXAM_CONTROLLER | INSTITUTE_ADMIN | SUPER_ADMIN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **View Own Academic Profile & Results** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **View Peer Student Results** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View Scoped Class Concept Mastery** | ❌ | ✅ (Scoped) | ✅ (Dept) | ❌ | ✅ | ✅ |
| **Create & Publish Assignments** | ❌ | ✅ (Scoped) | ✅ (Dept) | ❌ | ❌ | ✅ |
| **Submit Assignment Work** | ✅ (Self) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Grade & Evaluate Submissions** | ❌ | ✅ (Scoped) | ✅ (Dept) | ❌ | ❌ | ✅ |
| **Modify Published Results** | ❌ | ❌ | ✅ (Dual Control) | ❌ | ✅ (Audit Required) | ✅ (Audit Required) |
| **Create & Edit Question Bank** | ❌ | ✅ (Subject) | ✅ (Dept) | ✅ | ❌ | ✅ |
| **Publish Official MCAT Blueprint** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Attempt MCAT Assessment** | ✅ (Assigned) | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Monitor Live Exam Telemetry** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **Authorize New User Allowlist** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Deactivate / Reactivate User** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Revoke Active User Sessions** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **View Cryptographic Audit Trail** | ❌ | ❌ | ❌ | ❌ | ✅ (Read) | ✅ (Full) |
| **Run File Integrity Check** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Trigger System Backup** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Execute Database Restore** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Restricted) |
| **Query AROHAN AI Recommendations** | ✅ (Self) | ✅ (Class) | ✅ (Dept) | ❌ | ❌ | ✅ |

*Note: All permissions are enforced server-side. Frontend role representation is non-authoritative.*
