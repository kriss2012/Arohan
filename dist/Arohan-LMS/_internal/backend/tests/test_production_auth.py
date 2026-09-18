import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from backend.app.main import app
from backend.app.core.database import AsyncSessionLocal
from backend.app.models.user import User, EmailVerificationCode, PasswordResetToken

@pytest.mark.asyncio
async def test_production_auth_complete_scenarios():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        # -------------------------------------------------------------
        # SCENARIO C: Unauthorized user cannot access system
        # -------------------------------------------------------------
        unauth_resp = await ac.post("/api/v1/auth/check-email", json={"email": "random_intruder@unknown.org"})
        assert unauth_resp.status_code == 200
        unauth_data = unauth_resp.json()
        assert unauth_data["status"] == "UNAUTHORIZED"
        assert "access restricted" in unauth_data["message"].lower()

        # -------------------------------------------------------------
        # SCENARIO A: New Authorized User Lifecycle
        # 1. Check email -> FIRST_TIME_SETUP
        # 2. Receive 6-digit OTP
        # 3. Verify OTP -> get setup_token
        # 4. Mandatory Password Creation -> Dashboard session
        # -------------------------------------------------------------
        target_email = "rahul@imrd.ac.in"
        check_resp = await ac.post("/api/v1/auth/check-email", json={"email": target_email})
        assert check_resp.status_code == 200
        check_data = check_resp.json()
        assert check_data["status"] == "FIRST_TIME_SETUP"
        assert "•••••" in check_data["masked_email"]

        # Fetch the generated OTP code from the database for verification testing
        async with AsyncSessionLocal() as session:
            u_res = await session.execute(select(User).where(User.email == target_email))
            user = u_res.scalar_one_or_none()
            assert user is not None
            assert user.password_hash is None # Password NOT yet created
            assert user.is_email_verified is False

            c_res = await session.execute(
                select(EmailVerificationCode)
                .where(EmailVerificationCode.user_id == user.id, EmailVerificationCode.used_at.is_(None))
                .order_by(EmailVerificationCode.created_at.desc())
            )
            code_rec = c_res.scalar_one_or_none()
            assert code_rec is not None

        # Verify with wrong OTP fails
        bad_verify = await ac.post("/api/v1/auth/verify-code", json={
            "email": target_email,
            "code": "000000"
        })
        assert bad_verify.status_code == 400
        assert "incorrect" in bad_verify.json()["detail"].lower()

        # Verify with correct code:
        # In test, we can use the known code from EmailVerificationCode or create a known code
        # Let's inspect: AuthService hashes with sha256. If we test a known code:
        import hashlib
        known_code = "654321"
        async with AsyncSessionLocal() as session:
            active_c = (await session.execute(
                select(EmailVerificationCode)
                .where(EmailVerificationCode.user_id == user.id, EmailVerificationCode.used_at.is_(None))
                .order_by(EmailVerificationCode.created_at.desc())
            )).scalar_one()
            active_c.code_hash = hashlib.sha256(known_code.encode("utf-8")).hexdigest()
            await session.commit()

        verify_resp = await ac.post("/api/v1/auth/verify-code", json={
            "email": target_email,
            "code": known_code
        })
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        setup_token = verify_data["setup_token"]
        assert setup_token is not None

        # Test Password Policy: Weak password (< 12 chars) rejected
        weak_resp = await ac.post("/api/v1/auth/setup-password", json={
            "setup_token": setup_token,
            "password": "Short1!",
            "confirm_password": "Short1!"
        })
        assert weak_resp.status_code in [400, 422]

        # Test Password Policy: Missing special char rejected
        no_sym_resp = await ac.post("/api/v1/auth/setup-password", json={
            "setup_token": setup_token,
            "password": "PasswordWithoutSymbols123",
            "confirm_password": "PasswordWithoutSymbols123"
        })
        assert no_sym_resp.status_code == 400

        # Create compliant strong password
        new_valid_password = "RahulCampusPassword2026!"
        setup_resp = await ac.post("/api/v1/auth/setup-password", json={
            "setup_token": setup_token,
            "password": new_valid_password,
            "confirm_password": new_valid_password
        })
        assert setup_resp.status_code == 200
        setup_result = setup_resp.json()
        assert "access_token" in setup_result
        assert setup_result["user"]["email"] == target_email

        # -------------------------------------------------------------
        # SCENARIO B: Returning User Flow
        # Email check now returns ACTIVE_ACCOUNT, and password login works!
        # -------------------------------------------------------------
        check_again = await ac.post("/api/v1/auth/check-email", json={"email": target_email})
        assert check_again.status_code == 200
        assert check_again.json()["status"] == "ACTIVE_ACCOUNT"

        # Login with email + password
        login_resp = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": new_valid_password
        })
        assert login_resp.status_code == 200
        assert "access_token" in login_resp.json()

        # -------------------------------------------------------------
        # SCENARIO D: Wrong password rejected
        # -------------------------------------------------------------
        wrong_pw_resp = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": "WrongPassword123!"
        })
        assert wrong_pw_resp.status_code == 401
        assert "incorrect email or password" in wrong_pw_resp.json()["detail"].lower()

        # -------------------------------------------------------------
        # SCENARIO E: Deactivated User cannot log in
        # -------------------------------------------------------------
        # Admin logs in
        admin_login = await ac.post("/api/v1/auth/login", json={
            "email": "admin@imrd.ac.in",
            "password": "Admin@123"
        })
        admin_token = admin_login.json()["access_token"]
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Admin deactivates rahul
        async with AsyncSessionLocal() as session:
            u_res = await session.execute(select(User).where(User.email == target_email))
            rahul_user = u_res.scalar_one_or_none()
            rahul_id = rahul_user.id

        deact_resp = await ac.post(f"/api/v1/admin/users/{rahul_id}/deactivate", headers=headers)
        assert deact_resp.status_code == 200

        # Login rejected even with correct password
        blocked_login = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": new_valid_password
        })
        assert blocked_login.status_code == 403
        assert "inactive" in blocked_login.json()["detail"].lower()

        # Admin reactivates user
        react_resp = await ac.post(f"/api/v1/admin/users/{rahul_id}/reactivate", headers=headers)
        assert react_resp.status_code == 200

        # -------------------------------------------------------------
        # SCENARIO F: Forgot & Reset Password Flow
        # -------------------------------------------------------------
        forgot_resp = await ac.post("/api/v1/auth/forgot-password", json={"email": target_email})
        assert forgot_resp.status_code == 200

        # Set known reset code for test
        reset_code = "987654"
        async with AsyncSessionLocal() as session:
            r_res = await session.execute(
                select(PasswordResetToken)
                .where(PasswordResetToken.user_id == rahul_id, PasswordResetToken.used_at.is_(None))
                .order_by(PasswordResetToken.created_at.desc())
            )
            reset_rec = r_res.scalar_one_or_none()
            assert reset_rec is not None
            reset_rec.token_hash = hashlib.sha256(reset_code.encode("utf-8")).hexdigest()
            await session.commit()

        new_reset_pw = "ResetPasswordSecure2026!"
        reset_resp = await ac.post("/api/v1/auth/reset-password", json={
            "email": target_email,
            "reset_code": reset_code,
            "new_password": new_reset_pw,
            "confirm_password": new_reset_pw
        })
        assert reset_resp.status_code == 200

        # New password works!
        succ_reset_login = await ac.post("/api/v1/auth/login", json={
            "email": target_email,
            "password": new_reset_pw
        })
        assert succ_reset_login.status_code == 200
        assert "access_token" in succ_reset_login.json()
