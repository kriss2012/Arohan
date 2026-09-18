from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, create_refresh_token
from backend.app.models.user import User, UserRole, Department
from backend.app.schemas.auth import (
    CheckEmailRequest, CheckEmailResponse, 
    SendCodeRequest, SendCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    SetupPasswordRequest, ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ChangePasswordRequest,
    LoginRequest, Token, UserSummary
)
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterActivateRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    activation_code: str
    password: str
    first_name: str
    last_name: str

@router.post("/check-email", response_model=CheckEmailResponse)
async def check_email_state(
    payload: CheckEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Check account authorization and determine if user needs
    first-time verification + password creation or normal password login.
    """
    result = await AuthService.check_email(db, payload.email)
    return CheckEmailResponse(**result)

@router.post("/send-code", response_model=SendCodeResponse)
async def send_verification_code(
    payload: SendCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resends a 6-digit one-time verification code to authorized email."""
    result = await AuthService.send_verification_code(db, payload.email)
    return SendCodeResponse(**result)

@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    payload: VerifyCodeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Verify 6-digit OTP. Returns a short-lived setup token
    required for mandatory password setup.
    """
    setup_token = await AuthService.verify_code(db, payload.email, payload.code)
    return VerifyCodeResponse(
        setup_token=setup_token,
        message="Email verified successfully. Please create your password."
    )

@router.post("/setup-password", response_model=Token)
async def setup_first_time_password(
    payload: SetupPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Mandatory password creation for verified first-time users.
    Establishes password, activates account, creates authenticated session.
    """
    user = await AuthService.setup_password(
        db=db,
        setup_token=payload.setup_token,
        password=payload.password,
        confirm_password=payload.confirm_password
    )

    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == user.id))
    roles = list(roles_res.scalars().all())

    dept_name = None
    if user.department_id:
        dept_res = await db.execute(select(Department.name).where(Department.id == user.department_id))
        dept_name = dept_res.scalar_one_or_none()

    access_token = create_access_token(subject=user.id, roles=roles)
    refresh_token = create_refresh_token(subject=user.id)

    ip_addr = request.client.host if request.client else None
    await AuthService.create_session(db=db, user=user, refresh_token=refresh_token, ip_address=ip_addr)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 24 * 60,
        user=UserSummary(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            department_name=dept_name,
            institution_code="IMRD"
        )
    )

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Returning user password login with brute-force lockout protection."""
    ip_addr = request.client.host if request.client else None
    user = await AuthService.authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
        ip_address=ip_addr
    )

    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == user.id))
    roles = list(roles_res.scalars().all())

    dept_name = None
    if user.department_id:
        dept_res = await db.execute(select(Department.name).where(Department.id == user.department_id))
        dept_name = dept_res.scalar_one_or_none()

    access_token = create_access_token(subject=user.id, roles=roles)
    refresh_token = create_refresh_token(subject=user.id)

    await AuthService.create_session(db=db, user=user, refresh_token=refresh_token, ip_address=ip_addr)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 24 * 60,
        user=UserSummary(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            department_name=dept_name,
            institution_code="IMRD"
        )
    )

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Requests password reset code sent to authorized email."""
    await AuthService.forgot_password(db, payload.email)
    return ForgotPasswordResponse(
        message="If this email is authorized and active, a password reset verification code has been dispatched."
    )

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resets password using verification code and revokes all previous sessions."""
    await AuthService.reset_password(
        db=db,
        email=payload.email,
        reset_code=payload.reset_code,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password
    )
    return {"message": "Your password was changed successfully. You may now log in with your new credentials."}

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """In-app password change for authenticated users."""
    await AuthService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password
    )
    return {"message": "Password changed successfully. All other active sessions have been revoked."}

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Revokes active user sessions."""
    await AuthService.revoke_all_user_sessions(db, current_user.id)
    return {"message": "You have been securely signed out."}

@router.post("/logout-all")
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await AuthService.revoke_all_user_sessions(db, current_user.id)
    return {"message": "All user sessions successfully revoked."}

@router.get("/me", response_model=UserSummary)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == current_user.id))
    roles = list(roles_res.scalars().all())

    dept_name = None
    if current_user.department_id:
        dept_res = await db.execute(select(Department.name).where(Department.id == current_user.department_id))
        dept_name = dept_res.scalar_one_or_none()

    return UserSummary(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        roles=roles,
        department_name=dept_name,
        institution_code="IMRD"
    )

@router.post("/register-activate", response_model=Token)
async def register_and_activate(
    payload: RegisterActivateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Backward-compatible direct activation endpoint."""
    user = await AuthService.activate_account(
        db=db,
        email=payload.email,
        activation_code=payload.activation_code,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name
    )

    roles_res = await db.execute(select(UserRole.role_name).where(UserRole.user_id == user.id))
    roles = list(roles_res.scalars().all())

    access_token = create_access_token(subject=user.id, roles=roles)
    refresh_token = create_refresh_token(subject=user.id)

    await AuthService.create_session(db=db, user=user, refresh_token=refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 24 * 60,
        user=UserSummary(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            institution_code="IMRD"
        )
    )
