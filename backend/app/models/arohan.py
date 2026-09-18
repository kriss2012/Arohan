import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Recommendation(Base):
    __tablename__ = "arohan_recommendations"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    action_type = Column(String(50), default="GUIDED_PRACTICE") # PREREQUISITE_LEARN, GUIDED_PRACTICE, VALIDATION_ASSESSMENT, SPACED_REPETITION
    title = Column(String(200), nullable=False)
    evidence_summary = Column(Text, nullable=False)
    mathematical_rationale = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class FacultyIntervention(Base):
    __tablename__ = "faculty_interventions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    faculty_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    intervention_type = Column(String(50), default="REMEDIAL_PRACTICE")
    notes = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, ACCEPTED, COMPLETED
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class PlacementReadinessProfile(Base):
    __tablename__ = "placement_readiness_profiles"
    student_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    technical_score = Column(Float, default=0.0) # 0 to 100
    coding_score = Column(Float, default=0.0)
    aptitude_score = Column(Float, default=0.0)
    project_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)
    overall_readiness_index = Column(Float, default=0.0)
    evidence_verified = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), default=get_utc_now)
