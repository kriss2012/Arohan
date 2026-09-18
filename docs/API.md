# ISDP + AROHAN AI: REST API Specification

**Base URL**: `/api/v1`  
**Protocol**: HTTPS  
**Authentication Scheme**: Bearer `<JWT_ACCESS_TOKEN>`  
**Standard Response Headers**:
- `X-Server-Time-UTC`: Server-authoritative ISO-8601 timestamp
- `X-Request-ID`: Distributed correlation UUID

---

## 1. Authentication & Identity (`/api/v1/auth`)

### `POST /auth/login`
- **Access**: Public
- **Request Body**:
  ```json
  {
    "email": "student1@imrd.ac.in",
    "password": "Password@123"
  }
  ```
- **Response `200 OK`**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 900,
    "user": {
      "id": "u-101",
      "email": "student1@imrd.ac.in",
      "first_name": "Rohan",
      "last_name": "Patil",
      "roles": ["STUDENT"],
      "department_name": "Department of Computer Applications"
    }
  }
  ```

### `GET /auth/me`
- **Access**: Authenticated (Any Role)
- **Response `200 OK`**: Current user details, active roles, and institution affiliation.

---

## 2. Curriculum & Learning Resources (`/api/v1/curriculum`)

### `GET /curriculum/tree`
- **Access**: `STUDENT`, `FACULTY`, `HOD`, `INSTITUTE_ADMIN`
- **Query Params**: `program_id` (optional), `semester_id` (optional)
- **Response `200 OK`**: Hierarchical list of Subjects -> Units -> Topics with attached resources.

### `POST /curriculum/topics/{topic_id}/progress`
- **Access**: `STUDENT`
- **Request Body**:
  ```json
  {
    "status": "COMPLETED",
    "time_spent_seconds": 320
  }
  ```
- **Response `200 OK`**: Emits `StudentCompletedTopic` event into Evidence Engine.

---

## 3. MCAT Assessment Engine (`/api/v1/mcat`)

### `GET /mcat/exams`
- **Access**: `STUDENT`, `FACULTY`, `EXAM_CONTROLLER`
- **Response `200 OK`**: List of published aptitude exams, schedules, and student attempt status.

### `POST /mcat/attempts/start`
- **Access**: `STUDENT`
- **Request Body**:
  ```json
  {
    "exam_id": "exam-2026-diag-01"
  }
  ```
- **Response `201 Created`**: Creates or resumes attempt, transitions state to `STARTED`, returns questions (without answers) and server-authoritative remaining duration in seconds.

### `POST /mcat/attempts/{attempt_id}/save-response`
- **Access**: `STUDENT` (Owner of attempt)
- **Request Body**:
  ```json
  {
    "question_id": "q-quant-101",
    "selected_option_id": "opt-b",
    "is_marked_for_review": false,
    "response_time_seconds": 45.2
  }
  ```
- **Response `200 OK`**: Persists answer, verifies timestamp validity, detects response-time anomalies.

### `POST /mcat/attempts/{attempt_id}/integrity-event`
- **Access**: `STUDENT` (Client desktop/kiosk hook)
- **Request Body**:
  ```json
  {
    "event_type": "FOCUS_LOST",
    "severity": "LOW",
    "details": { "duration_seconds": 4.5, "target": "alt_tab" }
  }
  ```
- **Response `200 OK`**: Logs neutral integrity signal to attempt audit log.

### `POST /mcat/attempts/{attempt_id}/submit`
- **Access**: `STUDENT`
- **Response `200 OK`**:
  - Transitions attempt state `STARTED -> SUBMITTED -> AUTO_EVALUATED`.
  - Calculates raw score, domain scores (Quant, Logical, Verbal, DI), and IRT ability $\theta$.
  - Generates `StudentCompletedMCAT` evidence events.
  - Triggers Bayesian Knowledge Tracing updates and AROHAN recommendations.

---

## 4. AROHAN AI & Skill Diagnostics (`/api/v1/arohan`)

### `GET /arohan/recommendations`
- **Access**: `STUDENT`
- **Response `200 OK`**:
  ```json
  {
    "student_id": "u-101",
    "generated_at": "2026-09-18T08:30:00Z",
    "top_recommendations": [
      {
        "id": "rec-01",
        "skill_id": "sk-percentages",
        "skill_name": "Percentages",
        "action_type": "GUIDED_PRACTICE",
        "title": "Practice 10 High-Yield Percentage Problems",
        "evidence_summary": "Percentages mastery at 34% (MCAT accuracy: 33%). Prerequisite for upcoming Data Interpretation module.",
        "why_url": "/api/v1/arohan/evidence/sk-percentages"
      }
    ]
  }
  ```

### `GET /arohan/evidence/{skill_id}`
- **Access**: `STUDENT`, `FACULTY`, `MENTOR`
- **Response `200 OK`** (Evidence Drawer Data):
  ```json
  {
    "skill_name": "Percentages",
    "mastery_probability": 0.34,
    "confidence_score": 0.88,
    "evidence_count": 9,
    "recent_assessments": [
      { "name": "MCAT Diagnostic 2026", "score": "33% (1/3 correct)", "date": "2026-09-18" }
    ],
    "recommendation_logic": "Gap Score = 0.45*(1 - 0.34) + 0.20*(0.67 error) = 0.431. Exceeds intervention threshold 0.30."
  }
  ```

---

## 5. Faculty & Exam Controller Consoles

### `GET /faculty/class-performance`
- **Access**: `FACULTY`, `HOD`
- **Response `200 OK`**: Aggregate class competencies, concept gap heatmaps, students recommended for intervention.

### `POST /faculty/interventions`
- **Access**: `FACULTY`
- **Request Body**: Assigns guided remedial practice or notes to a struggling student.

### `GET /exam-controller/live-monitors`
- **Access**: `EXAM_CONTROLLER`, `SUPER_ADMIN`
- **Response `200 OK`**: Real-time stats across active exams: active candidates, disconnected sessions, submissions, integrity signal aggregates (low, medium, high).
