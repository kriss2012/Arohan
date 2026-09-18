from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AuthorizedUserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str
    intended_role: str # STUDENT, FACULTY, HOD, etc.
    department_id: Optional[str] = None
    program_id: Optional[str] = None
    academic_year_id: Optional[str] = None
    division_id: Optional[str] = None
    student_or_emp_id: Optional[str] = None

class AuthorizedUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    intended_role: str
    student_or_emp_id: Optional[str] = None
    activation_code: Optional[str] = None
    status: str
    invited_at: datetime
    used_at: Optional[datetime] = None

class BulkImportRow(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str
    intended_role: str
    student_or_emp_id: Optional[str] = None

class BulkImportValidationReport(BaseModel):
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    duplicates_in_csv: List[str] = []
    already_authorized_emails: List[str] = []
    errors: List[Dict[str, Any]] = []

class UserStatusUpdate(BaseModel):
    status: str # ACTIVE, INACTIVE, SUSPENDED, LOCKED

class DatabaseHealthOut(BaseModel):
    database_connected: bool
    database_engine: str
    active_connections: int
    total_users: int
    total_students: int
    total_faculty: int
    total_assignments: int
    total_submissions: int
    system_status: str

class StorageStatsOut(BaseModel):
    storage_root: str
    total_bytes: int
    category_breakdown: Dict[str, Any]

class BackupOut(BaseModel):
    backup_id: str
    filename: str
    size_bytes: int
    checksum_sha256: str
    total_files_archived: int
    timestamp: str
