# ISDP + AROHAN AI + MCAT: Product Requirements Document (PRD)

**Document Version**: 1.0.0  
**Status**: APPROVED FOR DEVELOPMENT  
**Target Environment**: Desktop First (Tauri) + Responsive Web  

---

## 1. System Overview & Core Philosophy

The **Institute Student Development Platform (ISDP)** is an institute-owned digital campus connecting academics, curriculum, learning, practice, assessments, coding, and placement preparation into one continuous evidence-based student-development journey.

**Core Philosophy**:
> *"AI recommends. Faculty guides. Student improves."*

---

## 2. Role-Based Access Matrix (8 Core Roles)

1. **SUPER_ADMIN**: Global system configuration, institutional tenant setup, disaster recovery.
2. **INSTITUTE_ADMIN**: Department administration, faculty allocations, academic calendars.
3. **HOD (Head of Department)**: Departmental curriculum oversight, aggregate student readiness, faculty workload metrics.
4. **FACULTY**: Course content authoring, assignment review, question bank authoring, manual intervention workflow.
5. **EXAM_CONTROLLER**: MCAT blueprint creation, live exam room monitoring, integrity signal reviews, result publishing.
6. **PLACEMENT_OFFICER**: Placement readiness radar, candidate shortlisting based on evidence, recruitment drives.
7. **MENTOR**: Direct student progress tracking, guidance notes, recommendation verification.
8. **STUDENT**: Command center, curriculum learning, MCAT examination room, AROHAN AI tutoring, evidence drawer.

---

## 3. Comprehensive Feature Specifications

### FEAT-001: Role-Based Authentication & Session Management
- **Role**: All Roles
- **User Story**: As a registered campus user, I want to securely log in with my institute credentials so that I can access my role-specific dashboard and actions.
- **Functional Requirements**:
  - Secure credential verification via Argon2/bcrypt.
  - Short-lived JWT access tokens (15 minutes) + rotating refresh tokens (7 days).
  - Multi-device session invalidation ("Logout from all devices").
  - Server-authoritative time synchronization header on all responses (`X-Server-Time-UTC`).
- **Database Requirements**: `users`, `roles`, `permissions`, `user_sessions`, `audit_logs`.
- **API Requirements**: `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`.
- **Security Requirements**: Constant-time comparison, brute-force rate-limiting (5 failed attempts per 10 min), HTTP-only secure cookies for tokens where supported.
- **Status**: IMPLEMENTED

---

### FEAT-002: Academic Curriculum & Resource Management Engine
- **Role**: STUDENT, FACULTY, HOD
- **User Story**: As a student, I want to navigate my degree program by semester, subject, and topic so that I can access approved learning materials and assignments.
- **Functional Requirements**:
  - Hierarchical structure: Institution -> Department -> Program -> Academic Year -> Semester -> Subject -> Unit -> Topic.
  - Resources attached to topics: PDF, notes, code examples, video links, practice problems.
  - Progress tracking: Opened, started, completed, time spent.
- **Database Requirements**: `programs`, `semesters`, `subjects`, `units`, `topics`, `resources`, `student_topic_progress`.
- **API Requirements**: `GET /api/v1/curriculum/tree`, `GET /api/v1/curriculum/topics/{id}`, `POST /api/v1/curriculum/topics/{id}/progress`.
- **UI Requirements**: Clean tree navigation, breadcrumbs, document viewer modal, reading time tracker.
- **Status**: IMPLEMENTED

---

### FEAT-003: MCAT Question Bank & Psychometric Calibration
- **Role**: FACULTY, EXAM_CONTROLLER
- **User Story**: As a faculty member or exam controller, I want to manage categorized aptitude questions with calibration parameters so that valid examinations can be authored.
- **Functional Requirements**:
  - Taxonomy: Quantitative, Logical, Verbal, Data Interpretation (with granular subcategories).
  - Question states: `DRAFT`, `AI_GENERATED`, `FACULTY_REVIEW`, `APPROVED`, `PUBLISHED`, `RETIRED`.
  - Item psychometrics: Facility index ($p$), discrimination index ($r_{\text{pbi}}$), 1PL/2PL Item Response Theory calibration parameters ($\theta, a, b$).
  - Question versioning: Any modification creates a new immutable version without mutating historical exam references.
- **Database Requirements**: `mcat_categories`, `questions`, `question_versions`, `question_options`, `item_psychometrics`.
- **API Requirements**: `GET /api/v1/mcat/questions`, `POST /api/v1/mcat/questions`, `POST /api/v1/mcat/questions/validate`.
- **Status**: IMPLEMENTED

---

### FEAT-004: MCAT Exam Blueprint & Secure 11-State Examination Lifecycle
- **Role**: EXAM_CONTROLLER, STUDENT
- **User Story**: As an exam controller, I want to publish balanced MCAT blueprints, and as a student, I want to take the exam in a resilient, secure environment.
- **Functional Requirements**:
  - Blueprint validation: Category distribution (e.g. 40% Quant, 35% Logical, 25% Verbal) and difficulty distribution (30% Easy, 50% Med, 20% Hard).
  - Strict 11-State FSM: `CREATED -> AUTHORIZED -> STARTED -> PAUSED -> INTERRUPTED -> RESUMED -> SUBMITTED -> AUTO_EVALUATED -> UNDER_REVIEW -> FINALIZED -> CANCELLED`.
  - Server-authoritative timer: Time remaining is calculated server-side; client manipulation has zero effect.
  - Resilient offline recovery: In case of transient network drop, answers and integrity events are encrypted locally and synchronized upon reconnection without losing state.
- **Database Requirements**: `mcat_blueprints`, `mcat_exams`, `mcat_attempts`, `mcat_responses`, `mcat_integrity_events`.
- **API Requirements**: `POST /api/v1/mcat/attempts/start`, `POST /api/v1/mcat/attempts/save-response`, `POST /api/v1/mcat/attempts/submit`.
- **Status**: IMPLEMENTED

---

### FEAT-005: Exam Integrity Logging & Review System
- **Role**: EXAM_CONTROLLER, STUDENT
- **User Story**: As an exam controller, I want to monitor candidate anomalies during exams without automatic, false accusations of cheating.
- **Functional Requirements**:
  - Desktop event listeners: Fullscreen exit, window focus lost, clipboard copy/paste attempt, unauthorized application launch attempt.
  - Statistical anomaly detection: Fast-response detection (e.g., 15 consecutive answers under 2 seconds) via IQR/Z-Score.
  - Event categorization: Low, Medium, High severity integrity signals.
  - Zero Automated Guilt: Platform records evidence; final determination is strictly human-in-the-loop.
- **Database Requirements**: `mcat_integrity_events`, `exam_audit_summaries`.
- **API Requirements**: `POST /api/v1/mcat/attempts/integrity-event`, `GET /api/v1/exam-controller/live-monitors`.
- **Status**: IMPLEMENTED

---

### FEAT-006: Student Evidence Engine & Bayesian Knowledge Tracing (BKT)
- **Role**: STUDENT, FACULTY
- **User Story**: As the system intelligence layer, I want to record all student interactions as immutable evidence and compute Bayesian mastery probabilities per skill.
- **Functional Requirements**:
  - Event types: `StudentViewedResource`, `StudentPassedCodingTest`, `StudentCompletedAssessment`, `StudentCompletedMCAT`.
  - BKT Formula:
    $$P(L_t | \text{Obs}) = \begin{cases} \frac{P(L_{t-1})(1 - P(S))}{P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)}, & \text{if Correct} \\ \frac{P(L_{t-1})P(S)}{P(L_{t-1})P(S) + (1 - P(L_{t-1}))(1 - P(G))}, & \text{if Incorrect} \end{cases}$$
    $$P(L_t) = P(L_t | \text{Obs}) + (1 - P(L_t | \text{Obs})) \cdot P(T)$$
  - Skill taxonomy: Quant, Logical, Verbal, Data Interpretation, Python, Java, SQL, Data Structures.
- **Database Requirements**: `student_events`, `skills`, `student_skill_competencies`, `bkt_parameters`.
- **API Requirements**: `POST /api/v1/evidence/ingest`, `GET /api/v1/skills/student/{student_id}`.
- **Status**: IMPLEMENTED

---

### FEAT-007: Skill-Gap Engine & Explainable AROHAN Recommendations
- **Role**: STUDENT, FACULTY
- **User Story**: As a student, I want personalized, top 3-5 learning actions explaining exactly why they were recommended with verifiable evidence.
- **Functional Requirements**:
  - Weighted Gap Score:
    $$\text{GapScore} = 0.45 \cdot \text{mastery\_gap} + 0.20 \cdot \text{error\_rate} + 0.15 \cdot \text{assessment\_weight} + 0.10 \cdot \text{coding\_weight} + 0.10 \cdot \text{recency}$$
  - Minimum evidence threshold: Status flags `INSUFFICIENT_EVIDENCE` if attempts $< 3$.
  - "Evidence Drawer" UI: Clicking "Why am I seeing this?" exposes exact mathematical reasons, MCAT scores, recent error logs, and syllabus prerequisites.
- **Database Requirements**: `student_skill_gaps`, `recommendations`, `faculty_interventions`.
- **API Requirements**: `GET /api/v1/arohan/recommendations`, `GET /api/v1/arohan/evidence/{skill_id}`.
- **Status**: IMPLEMENTED

---

### FEAT-008: Faculty Mentorship & Intervention Workflow
- **Role**: FACULTY
- **User Story**: As a professor, I want to review students struggling in my subjects and accept, modify, or assign personalized interventions.
- **Functional Requirements**:
  - Subject performance aggregation showing concept weakness clusters across the class.
  - Intervention actions: Assign remedial practice, schedule peer study, grant re-assessment.
  - Complete audit tracking of faculty-student interventions.
- **Database Requirements**: `faculty_interventions`, `class_skill_aggregates`.
- **API Requirements**: `GET /api/v1/faculty/classes/{id}/gaps`, `POST /api/v1/faculty/interventions`.
- **Status**: IMPLEMENTED

---

### FEAT-009: Multi-Dimensional Placement Readiness Indicator
- **Role**: PLACEMENT_OFFICER, STUDENT
- **User Story**: As a placement officer, I want an evidence-backed readiness radar across Technical, Coding, Aptitude, Projects, and Consistency without misleading placement guarantees.
- **Functional Requirements**:
  - Multi-dimensional radar score (0-100%) grounded entirely in verified student evidence.
  - Strict labeling: "Placement Readiness Indicator" — never labeled as "Placement Prediction" or "Guarantee".
- **Database Requirements**: `placement_readiness_profiles`, `placement_drives`.
- **API Requirements**: `GET /api/v1/placement/readiness/{student_id}`.
- **Status**: IMPLEMENTED
