import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True)
    actor_role = Column(String(50), nullable=True)
    action = Column(String(100), nullable=False) # LOGIN_SUCCESS, USER_AUTHORIZED, RESULT_PUBLISHED, TAMPER_ALERT, etc.
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    security_severity = Column(String(20), default="INFO") # INFO, LOW, MEDIUM, HIGH, CRITICAL
    previous_hash = Column(String(64), nullable=True) # Cryptographic hash chain link
    record_hash = Column(String(64), nullable=True)   # SHA-256(previous_hash + canonical_event_data)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)
