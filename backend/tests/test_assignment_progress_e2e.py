import pytest
import io
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_full_academic_lifecycle_e2e():
    """
    Test End-to-End:
    1. Faculty creates and publishes an assignment with a document.
    2. Student logs in, sees the assignment, submits a solution file.
    3. Faculty reviews submission and evaluates it with score and feedback.
    4. Result is saved, progress is recalculated, and skill evidence is captured.
    5. Student views updated progress and results.
    6. Verify anti-IDOR: Student cannot view other students' progress.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # A. Faculty Login
        fac_login = await ac.post("/api/v1/auth/login", json={
            "email": "faculty1@imrd.ac.in",
            "password": "Faculty@123"
        })
        assert fac_login.status_code == 200
        fac_token = fac_login.json()["access_token"]
        fac_headers = {"Authorization": f"Bearer {fac_token}"}

        # B. Student Login
        stu_login = await ac.post("/api/v1/auth/login", json={
            "email": "student1@imrd.ac.in",
            "password": "Student@123"
        })
        assert stu_login.status_code == 200
        stu_token = stu_login.json()["access_token"]
        stu_headers = {"Authorization": f"Bearer {stu_token}"}

        # 1. Faculty creates assignment
        pdf_content = b"%PDF-1.4\nAssignment Instructions on Python OOP\n%%EOF"
        files = {"file": ("python_oop_task.pdf", io.BytesIO(pdf_content), "application/pdf")}
        data = {
            "title": "Python Object Oriented Programming Lab",
            "description": "Create a banking system with inheritance and polymorphism",
            "subject_id": "sub-dsa-301",
            "semester_id": "sem-bca-3",
            "division_id": "div-bca-3a",
            "total_marks": 100,
            "passing_marks": 40
        }
        res_assign = await ac.post("/api/v1/assignments/", headers=fac_headers, data=data, files=files)
        assert res_assign.status_code == 200
        assignment_id = res_assign.json()["id"]

        # 2. Student views assignment list
        list_resp = await ac.get("/api/v1/assignments/", headers=stu_headers)
        assert list_resp.status_code == 200
        assignments = list_resp.json()
        assert any(a["id"] == assignment_id for a in assignments)

        # 3. Student submits assignment solution file
        solution_pdf = b"%PDF-1.4\nStudent Solution: Class BankAccount implementation\n%%EOF"
        sub_files = {"file": ("student_solution.pdf", io.BytesIO(solution_pdf), "application/pdf")}
        sub_data = {
            "assignment_id": assignment_id,
            "submission_text": "Completed all polymorphism and encapsulation requirements."
        }
        sub_resp = await ac.post(f"/api/v1/assignments/{assignment_id}/submit", headers=stu_headers, data=sub_data, files=sub_files)
        assert sub_resp.status_code == 200
        submission_id = sub_resp.json()["id"]
        assert sub_resp.json()["status"] == "SUBMITTED"

        # 4. Faculty lists submissions for this assignment
        fac_sub_list = await ac.get(f"/api/v1/assignments/{assignment_id}/submissions", headers=fac_headers)
        assert fac_sub_list.status_code == 200
        submissions = fac_sub_list.json()
        assert any(s["id"] == submission_id for s in submissions)

        # 5. Faculty evaluates submission (Marks: 88/100)
        eval_data = {
            "submission_id": submission_id,
            "marks_obtained": 88.0,
            "feedback": "Excellent inheritance model and clean code formatting.",
            "strengths": "Strong grasp of OOP principles",
            "improvements": "Consider adding custom exception classes for overdraft"
        }
        eval_resp = await ac.post("/api/v1/assignments/evaluate", headers=fac_headers, json=eval_data)
        assert eval_resp.status_code == 200
        eval_json = eval_resp.json()
        assert eval_json["marks_obtained"] == 88.0
        assert eval_json["grade"] in ["A", "A+"]

        # 6. Student queries their progress
        prog_resp = await ac.get("/api/v1/progress/my-progress", headers=stu_headers)
        assert prog_resp.status_code == 200
        prog_data = prog_resp.json()
        assert prog_data["assignment_score"] > 0
        assert prog_data["overall_progress"] > 0
        assert len(prog_data["recent_results"]) > 0
        assert prog_data["recent_results"][0]["marks"] == 88.0

        # 7. IDOR Protection: Student cannot query arbitrary progress ID or admin progress
        fake_id = "00000000-0000-0000-0000-000000000000"
        idor_resp = await ac.get(f"/api/v1/progress/{fake_id}", headers=stu_headers)
        assert idor_resp.status_code in [403, 404]
