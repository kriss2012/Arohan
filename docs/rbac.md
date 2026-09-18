# Role-Based Access Control (RBAC) Architecture

## 1. Institutional Roles
The platform implements 8 standardized institutional roles:
1. `SUPER_ADMIN` - Full system configuration, backup creation, restore, audit logs, and database maintenance.
2. `INSTITUTE_ADMIN` - User management, allowlist management, academic year setup, department oversight.
3. `HOD` - Head of Department; assigns faculty to subjects, reviews department-wide analytics, results, and student progress.
4. `FACULTY` - Manages assigned subjects/divisions, publishes assignments, evaluates submissions, enters grades.
5. `EXAM_CONTROLLER` - Manages examination schedules, publishes final results, oversees MCAT integrity.
6. `PLACEMENT_OFFICER` - Analyzes placement readiness, skill matrices, aptitude benchmarks.
7. `MENTOR` - Student counseling, progress monitoring, intervention recommendations.
8. `STUDENT` - Accesses enrolled courses, downloads material, submits assignments, takes MCAT, reviews personal feedback.

## 2. Granular Permissions Model
Permissions represent fine-grained capabilities stored in `permissions` and mapped via `role_permissions`:
- `USER_VIEW`, `USER_CREATE`, `USER_UPDATE`, `ROLE_ASSIGN`
- `STUDENT_VIEW`, `STUDENT_EDIT`, `FACULTY_VIEW`, `FACULTY_EDIT`
- `ASSIGNMENT_CREATE`, `ASSIGNMENT_VIEW`, `ASSIGNMENT_GRADE`, `SUBMISSION_VIEW`
- `RESULT_VIEW`, `RESULT_PUBLISH`
- `MCAT_CONDUCT`, `BACKUP_CREATE`, `BACKUP_RESTORE`, `SYSTEM_SETTINGS`

## 3. Data Scoping & Anti-IDOR Enforcement
Authorization is verified **strictly on the backend**:
- **Student Isolation**: Students can only access data where `student_id == current_user.id`. Direct attempts to view other students' progress or marks return `HTTP 403 Forbidden`.
- **Faculty Isolation**: Faculty can only create assignments or evaluate submissions for subjects explicitly linked in `faculty_subject_assignments`.
- **Zero Frontend Trust**: Frontend route guards or hidden buttons are treated solely as UI helpers; the backend re-verifies role and resource ownership on every API request.
