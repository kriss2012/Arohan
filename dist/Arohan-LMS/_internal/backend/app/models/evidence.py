import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Skill(Base):
    __tablename__ = "skills"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    category = Column(String(100), nullable=False) # QUANTITATIVE, LOGICAL, VERBAL, DATA_INTERPRETATION, TECHNICAL, CODING
    name = Column(String(150), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class BKTParameter(Base):
    __tablename__ = "bkt_parameters"
    skill_id = Column(String(36), ForeignKey("skills.id"), primary_key=True)
    p_l0 = Column(Float, default=0.10) # Prior probability
    p_t = Column(Float, default=0.15)  # Transition / Learning rate
    p_s = Column(Float, default=0.10)  # Slip probability
    p_g = Column(Float, default=0.20)  # Guess probability

class StudentSkillCompetency(Base):
    __tablename__ = "student_skill_competencies"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    mastery_probability = Column(Float, default=0.10) # P(L)
    confidence_score = Column(Float, default=0.50)
    evidence_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    last_updated = Column(DateTime(timezone=True), default=get_utc_now)

class StudentEvent(Base):
    __tablename__ = "student_events"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    event_type = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False) # MCAT, CURRICULUM, CODING_LAB, ASSIGNMENT
    skill_id = Column(String(36), nullable=True)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)
