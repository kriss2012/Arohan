# Institutional Authorization Architecture & Scoping Policy

## 1. Principles of Institutional Authorization

The authorization model follows three foundational rules:

1. **Deny by Default**: If no explicit permission or access grant exists for the authenticated role and resource, access is immediately rejected (`HTTP 403 Forbidden`).
2. **Context-Scoped Authorization**: Having a valid role (e.g. `FACULTY`) is insufficient on its own. Access is checked across:
   - **Role**: Does the user possess the required role?
   - **Departmental Scope**: Is the target resource within the faculty's assigned department?
   - **Subject Scope**: Is the faculty assigned to teach this specific subject/division?
   - **Resource Ownership**: Is the user accessing their own records or an authorized dependent entity?
3. **Server Authoritative Identity**: Never trust client-provided IDs (`userId`, `studentId`, `role`) in request bodies or query parameters. Identity is strictly derived from the validated JWT claims.

---

## 2. Authorization Pipeline Workflow

```
Incoming Request
       ↓
Extract & Verify JWT
       ↓
Load User & Active Roles from DB
       ↓
Check Account Active & Authorized?
       │   No → 403 Forbidden
       ↓ Yes
Check Role Matches Route Requirement?
       │   No → 403 Forbidden
       ↓ Yes
Check Resource Scope (Ownership / Division / Department):
  - Student: target_student_id == current_user.id
  - Faculty: faculty assigned to subject / division of student
  - Admin: institutional administrative grant
       │   No → 403 Forbidden
       ↓ Yes
Execute Business Logic
```

---

## 3. Self-Service vs Scoped Administrative Routes

### Self-Service Routes (Student & Faculty Personal)
- `/api/v1/curriculum/tree`: Scoped to student's enrolled program and semester.
- `/api/v1/arohan/recommendations`: Implicitly scoped to `current_user.id`.
- `/api/v1/arohan/evidence/{skill_id}`: Evaluates competencies for `current_user.id` only.
- `/api/v1/assignments`: Returns assignments assigned to the student's enrolled division.
- `/api/v1/files/{file_id}/download`: Validates that the requester has permission to view the parent assignment or submission.

### Scoped Academic Routes (Faculty)
- `/api/v1/faculty/class-summary`: Returns aggregated concept mastery for subjects assigned to the logged-in faculty member.
- `/api/v1/assignments/{id}/submissions`: Restricted to the faculty member who created the assignment or HOD of that department.
- `/api/v1/assignments/submissions/{id}/evaluate`: Requires assignment grader authorization.

### Global Administrative Routes
- `/api/v1/admin/users`: Restricted to `SUPER_ADMIN` and `INSTITUTE_ADMIN`.
- `/api/v1/admin/authorized-users`: Requires administrative grant.
- `/api/v1/security/*`: Restricted exclusively to system administrators.
