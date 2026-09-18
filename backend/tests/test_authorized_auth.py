import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app

@pytest.mark.asyncio
async def test_unauthorized_email_registration_blocked():
    """Verify that arbitrary public registration is strictly blocked (HTTP 403)"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/register-activate", json={
            "email": "intruder_hacker@unknown.org",
            "password": "SecurePassword123!",
            "first_name": "Intruder",
            "last_name": "Public",
            "activation_code": "ANY_CODE"
        })
        assert response.status_code == 403
        data = response.json()
        assert "allowlist" in data["detail"].lower()

@pytest.mark.asyncio
async def test_authorized_email_activation_flow():
    """Verify that an email in authorized_users can activate with correct code"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Admin login
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@imrd.ac.in",
            "password": "Admin@123"
        })
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["access_token"]

        # Admin adds authorized user
        auth_resp = await ac.post("/api/v1/admin/authorized-users", 
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "new_student_2026@imrd.ac.in",
                "full_name": "Rohan Deshmukh",
                "intended_role": "STUDENT"
            }
        )
        assert auth_resp.status_code == 200
        auth_data = auth_resp.json()
        act_code = auth_data["activation_code"]
        assert act_code is not None

        # Student activates account
        act_resp = await ac.post("/api/v1/auth/register-activate", json={
            "email": "new_student_2026@imrd.ac.in",
            "password": "StudentPassword123!",
            "first_name": "Rohan",
            "last_name": "Deshmukh",
            "activation_code": act_code
        })
        assert act_resp.status_code == 200
        user_data = act_resp.json()
        assert user_data["user"]["email"] == "new_student_2026@imrd.ac.in"

        # Student can now login
        login_resp = await ac.post("/api/v1/auth/login", json={
            "email": "new_student_2026@imrd.ac.in",
            "password": "StudentPassword123!"
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

@pytest.mark.asyncio
async def test_brute_force_lockout():
    """Verify that 5 failed login attempts lock the user account and admin can unlock"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        target_email = "student2@imrd.ac.in"
        for i in range(5):
            res = await ac.post("/api/v1/auth/login", json={
                "email": target_email,
                "password": "WrongPassword!!"
            })
            assert res.status_code == 401
        
        # 6th attempt should be locked (HTTP 403)
        res6 = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": "WrongPassword!!"
        })
        assert res6.status_code == 403
        assert "locked" in res6.json()["detail"].lower()

        # Unlock by Admin
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@imrd.ac.in",
            "password": "Admin@123"
        })
        token = admin_login.json()["access_token"]
        
        # Get target user id
        users_resp = await ac.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        users = users_resp.json()
        target_user = next(u for u in users if u["email"] == target_email)

        # Unlock API
        unlock_resp = await ac.post(f"/api/v1/admin/users/{target_user['id']}/unlock", headers={"Authorization": f"Bearer {token}"})
        assert unlock_resp.status_code == 200

        # User can now login with real password
        succ_login = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": "Student@123"
        })
        assert succ_login.status_code == 200
