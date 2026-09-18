from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Pattern allowing both public and local intranet domain extensions (e.g. .local, .lan, .edu.in)
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

class CheckEmailRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)

class CheckEmailResponse(BaseModel):
    status: str # NOT_FOUND, UNAUTHORIZED, INACTIVE, FIRST_TIME_SETUP, ACTIVE_ACCOUNT
    message: str
    masked_email: Optional[str] = None
    first_name: Optional[str] = None

class SendCodeRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)

class SendCodeResponse(BaseModel):
    message: str
    masked_email: str
    expires_in_seconds: int = 600

class VerifyCodeRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    code: str = Field(..., min_length=6, max_length=6)

class VerifyCodeResponse(BaseModel):
    setup_token: str
    message: str

class SetupPasswordRequest(BaseModel):
    setup_token: str
    password: str = Field(..., min_length=12)
    confirm_password: str

class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)

class ForgotPasswordResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    reset_code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=12)
    confirm_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)
    confirm_password: str

class LoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str

class UserSummary(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    department_name: Optional[str] = None
    institution_code: Optional[str] = "IMRD"

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    roles: List[str] = []
    exp: Optional[int] = None

class UserCreate(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: Optional[str] = None
    first_name: str
    last_name: str
    institution_id: str
    department_id: Optional[str] = None
    roles: List[str]
