import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text, Enum
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    departments = relationship("Department", back_populates="institution")
    users = relationship("User", back_populates="institution")

class Department(Base):
    __tablename__ = "departments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    
    institution = relationship("Institution", back_populates="departments")
    programs = relationship("Program", back_populates="department")
    users = relationship("User", back_populates="department")

class AcademicYear(Base):
    __tablename__ = "academic_years"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    year_code = Column(String(50), unique=True, nullable=False) # e.g. "2025-2026"
    is_current = Column(Boolean, default=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

class Division(Base):
    __tablename__ = "divisions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=False)
    name = Column(String(20), nullable=False) # e.g. "A", "B"
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)

class AuthorizedUser(Base):
    __tablename__ = "authorized_users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    intended_role = Column(String(50), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=True)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    division_id = Column(String(36), ForeignKey("divisions.id"), nullable=True)
    student_or_emp_id = Column(String(50), nullable=True)
    activation_code = Column(String(64), nullable=True)
    temporary_password_hash = Column(String(255), nullable=True)
    status = Column(String(50), default="INVITED") # INVITED, ACTIVE, USED, REVOKED, EXPIRED
    invited_by = Column(String(36), nullable=True)
    invited_at = Column(DateTime(timezone=True), default=get_utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True) # Nullable for newly authorized users before first-time password setup
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=True)
    profile_photo_path = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE") # INVITED, ACTIVE, INACTIVE, SUSPENDED, LOCKED
    is_authorized = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    password_created_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    institution = relationship("Institution", back_populates="users")
    department = relationship("Department", back_populates="users")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    student_profile = relationship("StudentProfile", uselist=False, back_populates="user")
    faculty_profile = relationship("FacultyProfile", uselist=False, back_populates="user")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class EmailVerificationCode(Base):
    __tablename__ = "email_verification_codes"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    code_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempt_count = Column(Integer, default=0)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    # SUPER_ADMIN, INSTITUTE_ADMIN, HOD, FACULTY, EXAM_CONTROLLER, PLACEMENT_OFFICER, MENTOR, STUDENT

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_name = Column(String(50), ForeignKey("roles.name"), primary_key=True)
    permission_name = Column(String(100), ForeignKey("permissions.name"), primary_key=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_name = Column(String(50), ForeignKey("roles.name"), primary_key=True)
    assigned_by = Column(String(36), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="roles")

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    refresh_token_hash = Column(String(255), nullable=False)
    device_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    user = relationship("User", back_populates="sessions")

class LoginEvent(Base):
    __tablename__ = "login_events"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True)
    email = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False) # LOGIN_SUCCESS, LOGIN_FAILED, ACCOUNT_LOCKED, LOGOUT
    device_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    failure_reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)

class Device(Base):
    __tablename__ = "devices"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_identifier = Column(String(100), unique=True, nullable=False)
    device_name = Column(String(100), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    os_name = Column(String(50), nullable=True)
    app_version = Column(String(50), nullable=True)
    status = Column(String(50), default="ACTIVE")
    registered_at = Column(DateTime(timezone=True), default=get_utc_now)
    last_seen_at = Column(DateTime(timezone=True), default=get_utc_now)

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    registration_number = Column(String(50), nullable=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=True)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=True)
    division_id = Column(String(36), ForeignKey("divisions.id"), nullable=True)
    current_cgpa = Column(Float, default=0.0)
    guardian_name = Column(String(100), nullable=True)
    guardian_phone = Column(String(30), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="student_profile")

class FacultyProfile(Base):
    __tablename__ = "faculty_profiles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True)
    designation = Column(String(100), default="Assistant Professor")
    specialization = Column(String(200), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    user = relationship("User", back_populates="faculty_profile")

class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=False)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=False)
    division_id = Column(String(36), ForeignKey("divisions.id"), nullable=True)
    enrollment_date = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="ACTIVE")

class FacultySubjectAssignment(Base):
    __tablename__ = "faculty_subject_assignments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    faculty_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=False)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=False)
    division_id = Column(String(36), ForeignKey("divisions.id"), nullable=True)
    assigned_by = Column(String(36), nullable=True)
    assigned_at = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="ACTIVE")
