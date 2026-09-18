import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_autonomous_user_journey(client: AsyncClient):
    print("\n=== [E2E STEP 1: Student Authentication (Pooja Chaudhari - BCA Sem 3)] ===")
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "student2@imrd.ac.in",
        "password": "Student@123"
    })
    assert login_res.status_code == 200
    student_data = login_res.json()
    student_token = student_data["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    assert student_data["user"]["first_name"] == "Pooja"
    print("Authenticated Student: Pooja Chaudhari")

    print("\n=== [E2E STEP 2: Explore Curriculum Syllabus Tree] ===")
    curr_res = await client.get("/api/v1/curriculum/tree", headers=student_headers)
    assert curr_res.status_code == 200
    subjects = curr_res.json()
    assert len(subjects) >= 3
    print(f"Curriculum Loaded: {len(subjects)} subjects active for BCA Sem 3.")

    print("\n=== [E2E STEP 3: Start MCAT Diagnostic Assessment Session] ===")
    exams_res = await client.get("/api/v1/mcat/exams", headers=student_headers)
    assert exams_res.status_code == 200
    exams = exams_res.json()
    assert len(exams) >= 1
    exam_id = exams[0]["id"]

    start_res = await client.post("/api/v1/mcat/attempts/start", json={"exam_id": exam_id}, headers=student_headers)
    assert start_res.status_code == 200
    attempt = start_res.json()
    attempt_id = attempt["id"]
    assert attempt["status"] == "STARTED"
    questions = attempt["questions"]
    assert len(questions) == 10
    print(f"MCAT Attempt Started: {attempt_id} with {len(questions)} questions.")

    print("\n=== [E2E STEP 4: Submit Answers & Test Response-Time Recording] ===")
    for idx, q in enumerate(questions[:4]):
        selected_opt = q["options"][1]["id"] # Option B
        save_res = await client.post(
            f"/api/v1/mcat/attempts/{attempt_id}/save-response",
            json={
                "question_id": q["id"],
                "selected_option_id": selected_opt,
                "is_marked_for_review": (idx == 1),
                "response_time_seconds": 25.0
            },
            headers=student_headers
        )
        assert save_res.status_code == 200

    print("\n=== [E2E STEP 5: Log Environmental Integrity Signal (Focus Lost Kiosk Simulation)] ===")
    sig_res = await client.post(
        f"/api/v1/mcat/attempts/{attempt_id}/integrity-event",
        json={
            "event_type": "FOCUS_LOST",
            "severity": "LOW",
            "details": {"duration_seconds": 3.8}
        },
        headers=student_headers
    )
    assert sig_res.status_code == 200
    assert sig_res.json()["severity"] == "LOW"
    print("Integrity Signal Logged as Neutral Audit Event.")

    print("\n=== [E2E STEP 6: Submit MCAT Attempt & Auto-Evaluate] ===")
    sub_res = await client.post(
        f"/api/v1/mcat/attempts/{attempt_id}/submit",
        headers=student_headers
    )
    assert sub_res.status_code == 200
    eval_res = sub_res.json()
    assert eval_res["status"] == "AUTO_EVALUATED"
    assert eval_res["integrity_signal_count"] >= 1
    assert "score_percentage" in eval_res
    print(f"Auto-Evaluation Complete: Score = {eval_res['score_percentage']}%, Total Correct = {eval_res['total_correct']}, Audit Signals = {eval_res['integrity_signal_count']}")

    print("\n=== [E2E STEP 7: Verify Student Competencies & AROHAN Recommendations Generated from Evidence] ===")
    comp_res = await client.get("/api/v1/arohan/competencies", headers=student_headers)
    assert comp_res.status_code == 200
    comps = comp_res.json()
    assert len(comps) >= 1
    print(f"Student Competencies Updated via BKT: {len(comps)} skills now tracked with posterior probabilities.")

    rec_res = await client.get("/api/v1/arohan/recommendations", headers=student_headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    if len(recs) > 0:
        top_rec = recs[0]
        print(f"Generated Recommendation: {top_rec['title']}")
        print(f"Evidence Summary: {top_rec['evidence_summary']}")
        
        # Test Evidence Drawer
        ev_res = await client.get(f"/api/v1/arohan/evidence/{top_rec['skill_id']}", headers=student_headers)
        assert ev_res.status_code == 200
        ev_data = ev_res.json()
        assert "mastery_probability" in ev_data
        print(f"Evidence Drawer Verified: P(L) = {ev_data['mastery_probability']}, Gap Score = {ev_data['gap_score']}")

    print("\n=== [E2E STEP 8: Faculty Console - Class Summary & Remedial Intervention] ===")
    faculty_login = await client.post("/api/v1/auth/login", json={
        "email": "faculty1@imrd.ac.in",
        "password": "Faculty@123"
    })
    faculty_headers = {"Authorization": f"Bearer {faculty_login.json()['access_token']}"}
    summary_res = await client.get("/api/v1/faculty/class-summary", headers=faculty_headers)
    assert summary_res.status_code == 200
    class_summary = summary_res.json()
    assert len(class_summary) >= 5
    print(f"Faculty Console: {len(class_summary)} concept domains monitored across the class.")

    intervene_res = await client.post(
        "/api/v1/faculty/interventions",
        json={
            "student_id": student_data["user"]["id"],
            "skill_id": "sk-percentages",
            "intervention_type": "REMEDIAL_PRACTICE",
            "notes": "Reviewed diagnostic MCAT: Please solve supplementary problem set on percentages."
        },
        headers=faculty_headers
    )
    assert intervene_res.status_code == 200
    print("Faculty Remedial Intervention Assigned Successfully.")

    print("\n=== [E2E STEP 9: Exam Controller Console - Live Monitors & Integrity Feed] ===")
    ctrl_login = await client.post("/api/v1/auth/login", json={
        "email": "controller@imrd.ac.in",
        "password": "Exam@123"
    })
    ctrl_headers = {"Authorization": f"Bearer {ctrl_login.json()['access_token']}"}
    monitor_res = await client.get("/api/v1/exam-controller/live-monitors", headers=ctrl_headers)
    assert monitor_res.status_code == 200
    mon_data = monitor_res.json()
    assert mon_data["active_candidates_count"] >= 1
    print(f"Live Monitor Stream: {mon_data['active_candidates_count']} total candidates, {len(mon_data['recent_integrity_signals'])} integrity signals audited.")

    print("\n=== [ALL END-TO-END AUTONOMOUS USER JOURNEYS FULLY VERIFIED] ===")
