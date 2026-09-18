import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "X-Server-Time-UTC" in response.headers
    assert "X-Request-ID" in response.headers

@pytest.mark.asyncio
async def test_student_login_and_me(client: AsyncClient):
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "student1@imrd.ac.in",
        "password": "Student@123"
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["first_name"] == "Rohan"
    assert "STUDENT" in data["user"]["roles"]

    token = data["access_token"]
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "student1@imrd.ac.in"

@pytest.mark.asyncio
async def test_curriculum_tree(client: AsyncClient):
    # Log in as student
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "student1@imrd.ac.in",
        "password": "Student@123"
    })
    token = login_resp.json()["access_token"]

    tree_resp = await client.get("/api/v1/curriculum/tree", headers={"Authorization": f"Bearer {token}"})
    assert tree_resp.status_code == 200
    subjects = tree_resp.json()
    assert len(subjects) >= 3
    # Check subjects contain units and topics
    subject_names = [s["name"] for s in subjects]
    assert "Data Structures & Algorithms" in subject_names

@pytest.mark.asyncio
async def test_complete_mcat_lifecycle(client: AsyncClient):
    # 1. Login student
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "student1@imrd.ac.in",
        "password": "Student@123"
    })
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Get available exams
    exams_resp = await client.get("/api/v1/mcat/exams", headers=auth_header)
    assert exams_resp.status_code == 200
    exams = exams_resp.json()
    assert len(exams) >= 1
    exam_id = exams[0]["id"]

    # 3. Start attempt
    start_resp = await client.post("/api/v1/mcat/attempts/start", json={"exam_id": exam_id}, headers=auth_header)
    assert start_resp.status_code == 200
    attempt_data = start_resp.json()
    attempt_id = attempt_data["id"]
    assert attempt_data["status"] == "STARTED"
    questions = attempt_data["questions"]
    assert len(questions) >= 5

    # 4. Save a response to question 1
    q1 = questions[0]
    opt_b = next((o for o in q1["options"] if o["option_key"] == "B"), q1["options"][0])
    save_resp = await client.post(
        f"/api/v1/mcat/attempts/{attempt_id}/save-response",
        json={
            "question_id": q1["id"],
            "selected_option_id": opt_b["id"],
            "is_marked_for_review": False,
            "response_time_seconds": 35.0
        },
        headers=auth_header
    )
    assert save_resp.status_code == 200

    # 5. Record a neutral integrity signal (e.g. Focus Lost)
    int_resp = await client.post(
        f"/api/v1/mcat/attempts/{attempt_id}/integrity-event",
        json={
            "event_type": "FOCUS_LOST",
            "severity": "LOW",
            "details": {"duration_seconds": 3.2}
        },
        headers=auth_header
    )
    assert int_resp.status_code == 200
    assert int_resp.json()["severity"] == "LOW"

    # 6. Submit exam attempt
    sub_resp = await client.post(
        f"/api/v1/mcat/attempts/{attempt_id}/submit",
        headers=auth_header
    )
    assert sub_resp.status_code == 200
    score_data = sub_resp.json()
    assert score_data["status"] == "AUTO_EVALUATED"
    assert "score_percentage" in score_data
    assert score_data["integrity_signal_count"] >= 1

@pytest.mark.asyncio
async def test_arohan_recommendations_and_evidence_drawer(client: AsyncClient):
    # Log in as student
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "student1@imrd.ac.in",
        "password": "Student@123"
    })
    token = login_resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # Get student recommendations
    rec_resp = await client.get("/api/v1/arohan/recommendations", headers=auth_header)
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert len(recs) >= 1
    top_rec = recs[0]
    assert "skill_id" in top_rec
    assert "mathematical_rationale" in top_rec

    # Open Evidence Drawer for that skill
    ev_resp = await client.get(f"/api/v1/arohan/evidence/{top_rec['skill_id']}", headers=auth_header)
    assert ev_resp.status_code == 200
    ev_data = ev_resp.json()
    assert ev_data["skill_id"] == top_rec["skill_id"]
    assert "mastery_probability" in ev_data
    assert "gap_score" in ev_data
    assert "recommendation_logic" in ev_data

@pytest.mark.asyncio
async def test_rbac_security_enforcement(client: AsyncClient):
    # Student attempting to access Exam Controller live monitor -> 403 Forbidden
    student_login = await client.post("/api/v1/auth/login", json={
        "email": "student1@imrd.ac.in",
        "password": "Student@123"
    })
    student_token = student_login.json()["access_token"]

    forbidden_resp = await client.get(
        "/api/v1/exam-controller/live-monitors",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert forbidden_resp.status_code == 403

    # Exam Controller accessing -> 200 OK
    ctrl_login = await client.post("/api/v1/auth/login", json={
        "email": "controller@imrd.ac.in",
        "password": "Exam@123"
    })
    ctrl_token = ctrl_login.json()["access_token"]

    ok_resp = await client.get(
        "/api/v1/exam-controller/live-monitors",
        headers={"Authorization": f"Bearer {ctrl_token}"}
    )
    assert ok_resp.status_code == 200
    data = ok_resp.json()
    assert "active_candidates_count" in data
    assert "candidates" in data
