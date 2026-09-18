import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Result(Base):
    __tablename__ = "results"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    assessment_id = Column(String(36), nullable=True)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=True)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=True)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade = Column(String(10), nullable=False)
    grade_point = Column(Float, default=0.0)
    result_status = Column(String(50), default="PASSED")
    published = Column(Boolean, default=True)
    published_at = Column(DateTime(timezone=True), default=get_utc_now)
    published_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class ProgressWeightConfig(Base):
    __tablename__ = "progress_weight_configs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    assignment_weight = Column(Float, default=0.20) # 20%
    assessment_weight = Column(Float, default=0.25) # 25%
    mcat_weight = Column(Float, default=0.15)       # 15%
    coding_weight = Column(Float, default=0.15)     # 15%
    project_weight = Column(Float, default=0.15)    # 15%
    activity_weight = Column(Float, default=0.10)   # 10%
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now)

class StudentProgress(Base):
    __tablename__ = "student_progress"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=True)
    unit_id = Column(String(36), ForeignKey("units.id"), nullable=True)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=True)
    overall_progress = Column(Float, default=0.0) # 0 to 100%
    completion_percentage = Column(Float, default=0.0)
    mastery_score = Column(Float, default=0.0)
    assessment_score = Column(Float, default=0.0)
    assignment_score = Column(Float, default=0.0)
    mcat_score = Column(Float, default=0.0)
    coding_score = Column(Float, default=0.0)
    project_score = Column(Float, default=0.0)
    activity_score = Column(Float, default=0.0)
    consistency_score = Column(Float, default=85.0)
    last_activity_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

class LearningActivity(Base):
    __tablename__ = "learning_activities"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=True)
    resource_id = Column(String(36), ForeignKey("resources.id"), nullable=True)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=True)
    assessment_id = Column(String(36), nullable=True)
    activity_type = Column(String(100), nullable=False)
    started_at = Column(DateTime(timezone=True), default=get_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, default=0)
    progress_percentage = Column(Float, default=100.0)
    metadata_json = Column(Text, nullable=True)

class SkillEvidence(Base):
    __tablename__ = "skill_evidence"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False)
    source_type = Column(String(50), nullable=False) # MCAT, ASSESSMENT, ASSIGNMENT, CODING, PROJECT, PRACTICE, FACULTY_EVALUATION
    source_id = Column(String(36), nullable=True)
    score = Column(Float, nullable=False)
    normalized_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.80)
    evidence_weight = Column(Float, default=1.0)
    recorded_at = Column(DateTime(timezone=True), default=get_utc_now)
    metadata_json = Column(Text, nullable=True)

class ResultVersion(Base):
    __tablename__ = "result_versions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    result_id = Column(String(36), ForeignKey("results.id"), nullable=False)
    version = Column(Integer, nullable=False)
    marks = Column(Float, nullable=False)
    max_marks = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade = Column(String(10), nullable=False)
    change_reason = Column(Text, nullable=False)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)

class GradingPolicy(Base):
    __tablename__ = "grading_policies"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), default="Standard Institutional 10-Point Scale")
    version = Column(String(20), default="v1.0") # e.g. v1.0
    min_o = Column(Float, default=90.0)  # O: 90.00% - 100%
    min_ap = Column(Float, default=80.0) # A+: 80.00% - 89.99%
    min_a = Column(Float, default=70.0)  # A: 70.00% - 79.99%
    min_bp = Column(Float, default=60.0) # B+: 60.00% - 69.99%
    min_b = Column(Float, default=55.0)  # B: 55.00% - 59.99%
    min_c = Column(Float, default=50.0)  # C: 50.00% - 54.99%
    min_p = Column(Float, default=40.0)  # P: 40.00% - 49.99%
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
