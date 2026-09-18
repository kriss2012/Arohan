import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, BigInteger, Text, Boolean
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class FileRecord(Base):
    __tablename__ = "files"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), unique=True, nullable=False)
    storage_path = Column(Text, nullable=False) # Local relative or absolute path
    mime_type = Column(String(100), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(50), nullable=True) # ASSIGNMENT, SUBMISSION, RESOURCE, BACKUP, PROFILE
    entity_id = Column(String(36), nullable=True)
    version = Column(Integer, default=1)
    status = Column(String(50), default="ACTIVE") # ACTIVE, ARCHIVED, DELETED
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class FileVersion(Base):
    __tablename__ = "file_versions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    checksum_sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="ARCHIVED")

class DocumentPermission(Base):
    __tablename__ = "document_permissions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    role_id = Column(Integer, nullable=True)
    student_id = Column(String(36), nullable=True)
    department_id = Column(String(36), nullable=True)
    program_id = Column(String(36), nullable=True)
    division_id = Column(String(36), nullable=True)
    subject_id = Column(String(36), nullable=True)
    access_type = Column(String(20), default="VIEW") # VIEW, DOWNLOAD, EDIT, DELETE
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
