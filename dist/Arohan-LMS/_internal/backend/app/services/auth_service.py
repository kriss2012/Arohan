import hashlib
import secrets
import uuid
import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from backend.app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, create_setup_token, decode_token
)
from backend.app.models.user import (
    User, AuthorizedUser, UserRole, UserSession, 
    LoginEvent, StudentProfile, FacultyProfile,
    EmailVerificationCode, PasswordResetToken
)
from backend.app.services.email_service import EmailService

LOCKOUT_THRESHOLD = 5
LOCKOUT_MINUTES = 15
OTP_EXPIRATION_MINUTES = 10
RESET_TOKEN_EXPIRATION_MINUTES = 15

COMMON_WEAK_PASSWORDS = {
    "password123!", "admin123456!", "college12345!", "welcome12345!",
    "123456789012!", "qwertyuiop12!"
}

class AuthService:
    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def mask_email(email: str) -> str:
        """Masks email like r•••••@imrd.ac.in"""
        if "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 1:
            masked_local = local + "••••"
        else:
            masked_local = local[0] + "•••••"
        return f"{masked_local}@{domain}"

    @staticmethod
    def validate_password_policy(password: str) -> Tuple[bool, str]:
        """
        Validates production password criteria:
        - Minimum 12 characters
        - Uppercase, Lowercase, Number, Special character
        - Not in common weak list
        """
        if len(password) < 12:
            return False, "Password must be at least 12 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter (A-Z)."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter (a-z)."
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one numeric digit (0-9)."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            return False, "Password must contain at least one special character (!@#$%^&* etc.)."
        if password.lower() in COMMON_WEAK_PASSWORDS:
            return False, "This password is too common or easily guessed. Please choose a stronger password."
        return True, ""

    @staticmethod
    async def is_email_authorized(db: AsyncSession, email: str) -> Optional[AuthorizedUser]:
        clean_email = email.strip().lower()
        result = await db.execute(
            select(AuthorizedUser).where(
                AuthorizedUser.email.ilike(clean_email),
                AuthorizedUser.status.in_(["INVITED", "ACTIVE", "USED"])
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def check_email(cls, db: AsyncSession, email: str) -> Dict[str, Any]:
        """
        Determines account state without revealing sensitive internal details.
        Returns state: NOT_FOUND, UNAUTHORIZED, INACTIVE, FIRST_TIME_SETUP, ACTIVE_ACCOUNT
        """
        clean_email = email.strip().lower()
        masked = cls.mask_email(clean_email)

        # 1. Check if user already exists
        u_res = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = u_res.scalar_one_or_none()

        if user:
            if not user.is_active or user.status in ["SUSPENDED", "INACTIVE"]:
                return {
                    "status": "INACTIVE",
                    "message": "Account unavailable: This account is currently inactive. Please contact your administrator.",
                    "masked_email": masked
                }
            if not user.is_authorized:
                return {
                    "status": "UNAUTHORIZED",
                    "message": "Access restricted: This account is not authorized to access the system. Please contact your administrator.",
                    "masked_email": masked
                }
            
            # If user has no password or unverified email, they need first-time setup
            if not user.password_hash or not user.is_email_verified:
                # Trigger verification code dispatch
                await cls.send_verification_code(db, clean_email)
                return {
                    "status": "FIRST_TIME_SETUP",
                    "message": "We've sent a one-time verification code to your authorized email address.",
                    "masked_email": masked,
                    "first_name": user.first_name
                }
            
            # Otherwise, standard password login
            return {
                "status": "ACTIVE_ACCOUNT",
                "message": "Enter your password to continue.",
                "masked_email": masked,
                "first_name": user.first_name
            }

        # 2. User not in users table: check authorized_users allowlist
        auth_entry = await cls.is_email_authorized(db, clean_email)
        if not auth_entry:
            return {
                "status": "UNAUTHORIZED",
                "message": "Access restricted: This email address is not currently authorized to access this system. Please contact your administrator if you believe you should have access.",
                "masked_email": masked
            }

        # Auto-provision pending first-time setup account from allowlist
        names = (auth_entry.full_name or "New Member").split(" ", 1)
        fname = names[0]
        lname = names[1] if len(names) > 1 else "Student"

        new_user = User(
            id=str(uuid.uuid4()),
            institution_id="inst-imrd-01",
            department_id=auth_entry.department_id,
            email=clean_email,
            password_hash=None, # Explicitly NULL until password setup
            first_name=fname,
            last_name=lname,
            status="INVITED",
            is_authorized=True,
            is_active=True,
            email_verified=False,
            is_email_verified=False
        )
        db.add(new_user)
        await db.flush()

        # Assign intended role
        db.add(UserRole(user_id=new_user.id, role_name=auth_entry.intended_role or "STUDENT"))

        # Provision profile
        if auth_entry.intended_role == "STUDENT":
            db.add(StudentProfile(
                user_id=new_user.id,
                student_id=auth_entry.student_or_emp_id or f"STU-{uuid.uuid4().hex[:6].upper()}",
                roll_number=auth_entry.student_or_emp_id or f"ROLL-{uuid.uuid4().hex[:4].upper()}",
                department_id=auth_entry.department_id,
                program_id=auth_entry.program_id,
                academic_year_id=auth_entry.academic_year_id,
                division_id=auth_entry.division_id
            ))
        elif auth_entry.intended_role == "FACULTY":
            db.add(FacultyProfile(
                user_id=new_user.id,
                employee_id=auth_entry.student_or_emp_id or f"EMP-{uuid.uuid4().hex[:6].upper()}",
                department_id=auth_entry.department_id
            ))

        await db.commit()
        await db.refresh(new_user)

        # Trigger verification code dispatch
        await cls.send_verification_code(db, clean_email)

        return {
            "status": "FIRST_TIME_SETUP",
            "message": "We've sent a one-time verification code to your authorized email address.",
            "masked_email": masked,
            "first_name": fname
        }

    @classmethod
    async def send_verification_code(cls, db: AsyncSession, email: str) -> Dict[str, Any]:
        """Generates a secure 6-digit random code, hashes it, stores in DB, sends email."""
        clean_email = email.strip().lower()
        u_res = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = u_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User account not found.")

        # Cryptographically secure 6-digit code
        raw_code = f"{secrets.randbelow(900000) + 100000}"
        code_hash = cls.hash_token(raw_code)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)

        # Invalidate previous unused codes for this user
        await db.execute(
            update(EmailVerificationCode)
            .where(EmailVerificationCode.user_id == user.id, EmailVerificationCode.used_at.is_(None))
            .values(used_at=now)
        )

        otp_rec = EmailVerificationCode(
            user_id=user.id,
            code_hash=code_hash,
            expires_at=expires,
            attempt_count=0,
            created_at=now
        )
        db.add(otp_rec)
        await db.commit()

        # Send email
        EmailService.send_verification_code_email(
            to_email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            code=raw_code
        )

        return {
            "message": "Verification code sent to authorized email address.",
            "masked_email": cls.mask_email(user.email),
            "expires_in_seconds": OTP_EXPIRATION_MINUTES * 60
        }

    @classmethod
    async def verify_code(cls, db: AsyncSession, email: str, code: str) -> str:
        """
        Verifies 6-digit code.
        Enforces maximum 5 attempts and 10-minute expiration.
        Returns a short-lived setup token required for mandatory password creation.
        """
        clean_email = email.strip().lower()
        u_res = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = u_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid verification request.")

        # Get latest unused code
        c_res = await db.execute(
            select(EmailVerificationCode)
            .where(EmailVerificationCode.user_id == user.id, EmailVerificationCode.used_at.is_(None))
            .order_by(EmailVerificationCode.created_at.desc())
        )
        otp_entry = c_res.scalar_one_or_none()
        if not otp_entry:
            raise HTTPException(status_code=400, detail="No active verification code found. Please request a new code.")

        now = datetime.now(timezone.utc)
        exp_time = otp_entry.expires_at if otp_entry.expires_at.tzinfo else otp_entry.expires_at.replace(tzinfo=timezone.utc)

        if now > exp_time or otp_entry.attempt_count >= 5:
            otp_entry.used_at = now
            await db.commit()
            raise HTTPException(status_code=400, detail="Verification code has expired or exceeded maximum attempts. Please request a new code.")

        otp_entry.attempt_count += 1
        provided_hash = cls.hash_token(code.strip())

        if provided_hash != otp_entry.code_hash:
            await db.commit()
            remaining = 5 - otp_entry.attempt_count
            raise HTTPException(status_code=400, detail=f"Incorrect verification code. {remaining} attempt(s) remaining.")

        # Mark code used
        otp_entry.used_at = now
        await db.commit()

        # Issue short-lived setup_token (15 min)
        setup_token = create_setup_token(subject=user.id, email=user.email, expires_delta=timedelta(minutes=15))
        return setup_token

    @classmethod
    async def setup_password(
        cls, 
        db: AsyncSession, 
        setup_token: str, 
        password: str, 
        confirm_password: str
    ) -> User:
        """
        Validates setup_token and establishes the mandatory password for first-time activation.
        """
        payload = decode_token(setup_token)
        if not payload or payload.get("purpose") != "password_setup":
            raise HTTPException(status_code=400, detail="Invalid or expired setup session. Please verify your email again.")

        user_id = payload.get("sub")
        u_res = await db.execute(select(User).where(User.id == user_id))
        user = u_res.scalar_one_or_none()
        if not user or not user.is_active or not user.is_authorized:
            raise HTTPException(status_code=403, detail="Account is not eligible for setup.")

        if password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        is_valid, msg = cls.validate_password_policy(password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        now = datetime.now(timezone.utc)
        user.password_hash = get_password_hash(password)
        user.password_created_at = now
        user.password_changed_at = now
        user.email_verified = True
        user.is_email_verified = True
        user.email_verified_at = now
        user.status = "ACTIVE"

        # Mark corresponding authorized_users record as USED
        await db.execute(
            update(AuthorizedUser)
            .where(AuthorizedUser.email == user.email)
            .values(status="USED", used_at=now)
        )

        await db.commit()
        await db.refresh(user)

        # Record login event
        db.add(LoginEvent(
            user_id=user.id,
            email=user.email,
            event_type="PASSWORD_CREATED",
            failure_reason="First-time setup completed successfully"
        ))
        await db.commit()

        return user

    @classmethod
    async def authenticate_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> User:
        clean_email = email.strip().lower()
        result = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if not user:
            db.add(LoginEvent(
                email=clean_email,
                event_type="LOGIN_FAILED",
                ip_address=ip_address,
                device_id=device_id,
                failure_reason="User not found"
            ))
            await db.commit()
            raise HTTPException(status_code=401, detail="Incorrect email or password. Please check your credentials and try again.")

        # Check account lock status
        if user.locked_until:
            lock_time = user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=timezone.utc)
            if lock_time > now:
                diff_mins = int((lock_time - now).total_seconds() / 60) + 1
                db.add(LoginEvent(
                    user_id=user.id,
                    email=clean_email,
                    event_type="ACCOUNT_LOCKED",
                    ip_address=ip_address,
                    device_id=device_id,
                    failure_reason="Attempt while locked"
                ))
                await db.commit()
                raise HTTPException(
                    status_code=403, 
                    detail=f"Account is temporarily locked due to repeated failed attempts. Try again in {diff_mins} minutes or contact administrator."
                )

        if not user.is_active or user.status in ["SUSPENDED", "INACTIVE"]:
            raise HTTPException(status_code=403, detail="Account unavailable: This account is currently inactive. Please contact your administrator.")

        if not user.is_authorized:
            raise HTTPException(status_code=403, detail="Access restricted: This account is not authorized to access the system. Please contact your administrator.")

        if not user.password_hash:
            raise HTTPException(status_code=403, detail="First-time setup required. Please verify your email first.")

        # Verify password
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= LOCKOUT_THRESHOLD:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                user.status = "LOCKED"
                event_type = "ACCOUNT_LOCKED"
                fail_msg = f"Account locked after {LOCKOUT_THRESHOLD} failed attempts"
            else:
                event_type = "LOGIN_FAILED"
                fail_msg = f"Incorrect password ({user.failed_login_attempts}/{LOCKOUT_THRESHOLD})"

            db.add(LoginEvent(
                user_id=user.id,
                email=clean_email,
                event_type=event_type,
                ip_address=ip_address,
                device_id=device_id,
                failure_reason=fail_msg
            ))
            await db.commit()
            raise HTTPException(status_code=401, detail="Incorrect email or password. Please check your credentials and try again.")

        # Login succeeded: reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        if user.status == "LOCKED":
            user.status = "ACTIVE"
        user.last_login_at = now

        db.add(LoginEvent(
            user_id=user.id,
            email=clean_email,
            event_type="LOGIN_SUCCESS",
            ip_address=ip_address,
            device_id=device_id
        ))
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def forgot_password(cls, db: AsyncSession, email: str) -> None:
        """Sends secure 6-digit password reset code."""
        clean_email = email.strip().lower()
        u_res = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = u_res.scalar_one_or_none()

        # If user doesn't exist or is inactive, silently succeed to prevent user enumeration
        if not user or not user.is_active or not user.is_authorized:
            return

        raw_code = f"{secrets.randbelow(900000) + 100000}"
        token_hash = cls.hash_token(raw_code)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=RESET_TOKEN_EXPIRATION_MINUTES)

        # Invalidate previous tokens
        await db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
            .values(used_at=now)
        )

        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires,
            created_at=now
        )
        db.add(reset_entry)
        await db.commit()

        EmailService.send_password_reset_email(
            to_email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            reset_code=raw_code
        )

    @classmethod
    async def reset_password(
        cls, 
        db: AsyncSession, 
        email: str, 
        reset_code: str, 
        new_password: str, 
        confirm_password: str
    ) -> None:
        """Resets password using 6-digit reset code and revokes all previous sessions."""
        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match.")

        is_valid, msg = cls.validate_password_policy(new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        clean_email = email.strip().lower()
        u_res = await db.execute(select(User).where(User.email.ilike(clean_email)))
        user = u_res.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=400, detail="Invalid password reset request.")

        # Find valid token
        c_res = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None))
            .order_by(PasswordResetToken.created_at.desc())
        )
        token_entry = c_res.scalar_one_or_none()
        if not token_entry:
            raise HTTPException(status_code=400, detail="Invalid or expired reset code. Please request a new code.")

        now = datetime.now(timezone.utc)
        exp_time = token_entry.expires_at if token_entry.expires_at.tzinfo else token_entry.expires_at.replace(tzinfo=timezone.utc)

        if now > exp_time or token_entry.token_hash != cls.hash_token(reset_code.strip()):
            raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

        # Update password
        token_entry.used_at = now
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = now

        # Revoke all existing sessions
        await cls.revoke_all_user_sessions(db, user.id)

        db.add(LoginEvent(
            user_id=user.id,
            email=user.email,
            event_type="PASSWORD_RESET_SUCCESS",
            failure_reason="Password reset via verification code"
        ))
        await db.commit()

        EmailService.send_password_changed_email(user.email, f"{user.first_name} {user.last_name}")

    @classmethod
    async def change_password(
        cls, 
        db: AsyncSession, 
        user: User, 
        current_password: str, 
        new_password: str, 
        confirm_password: str
    ) -> None:
        """In-app password change for authenticated users."""
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password does not match.")

        if new_password != confirm_password:
            raise HTTPException(status_code=400, detail="New passwords do not match.")

        is_valid, msg = cls.validate_password_policy(new_password)
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        now = datetime.now(timezone.utc)
        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = now

        # Revoke other sessions
        await cls.revoke_all_user_sessions(db, user.id)

        db.add(LoginEvent(
            user_id=user.id,
            email=user.email,
            event_type="PASSWORD_CHANGED",
            failure_reason="User updated password via settings"
        ))
        await db.commit()

        EmailService.send_password_changed_email(user.email, f"{user.first_name} {user.last_name}")

    @classmethod
    async def activate_account(
        cls,
        db: AsyncSession,
        email: str,
        activation_code: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Backward-compatible direct activation method."""
        auth_entry = await cls.is_email_authorized(db, email)
        if not auth_entry:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email is not on the institutional authorized allowlist. Contact administrator."
            )

        if auth_entry.activation_code and auth_entry.activation_code != activation_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid activation code."
            )

        existing_res = await db.execute(select(User).where(User.email == email))
        user = existing_res.scalar_one_or_none()

        if user and user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account has already been activated. Please log in directly."
            )

        if not first_name or not last_name:
            names = (auth_entry.full_name or "New Member").split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else "Student"

        now = datetime.now(timezone.utc)
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                institution_id="inst-imrd-01",
                department_id=auth_entry.department_id,
                email=email,
                password_hash=get_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                status="ACTIVE",
                is_authorized=True,
                is_active=True,
                email_verified=True,
                is_email_verified=True,
                password_created_at=now,
                password_changed_at=now
            )
            db.add(user)
            await db.flush()

            db.add(UserRole(user_id=user.id, role_name=auth_entry.intended_role or "STUDENT"))

            if auth_entry.intended_role == "STUDENT":
                db.add(StudentProfile(
                    user_id=user.id,
                    student_id=auth_entry.student_or_emp_id or f"STU-{uuid.uuid4().hex[:6].upper()}",
                    roll_number=auth_entry.student_or_emp_id or f"ROLL-{uuid.uuid4().hex[:4].upper()}",
                    department_id=auth_entry.department_id,
                    program_id=auth_entry.program_id,
                    academic_year_id=auth_entry.academic_year_id,
                    division_id=auth_entry.division_id
                ))
            elif auth_entry.intended_role == "FACULTY":
                db.add(FacultyProfile(
                    user_id=user.id,
                    employee_id=auth_entry.student_or_emp_id or f"EMP-{uuid.uuid4().hex[:6].upper()}",
                    department_id=auth_entry.department_id
                ))
        else:
            user.password_hash = get_password_hash(password)
            user.status = "ACTIVE"
            user.is_authorized = True
            user.is_active = True
            user.email_verified = True
            user.is_email_verified = True
            user.password_created_at = now
            user.password_changed_at = now

        auth_entry.status = "USED"
        auth_entry.used_at = now
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user: User,
        refresh_token: str,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> UserSession:
        now = datetime.now(timezone.utc)
        session_rec = UserSession(
            user_id=user.id,
            refresh_token_hash=cls.hash_token(refresh_token),
            device_id=device_id,
            ip_address=ip_address,
            is_revoked=False,
            expires_at=now + timedelta(days=7),
            last_activity_at=now
        )
        db.add(session_rec)
        await db.commit()
        return session_rec

    @classmethod
    async def revoke_all_user_sessions(cls, db: AsyncSession, user_id: str) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(UserSession)
            .where(UserSession.user_id == user_id, UserSession.is_revoked == False)
            .values(is_revoked=True, revoked_at=now)
        )
        await db.commit()
