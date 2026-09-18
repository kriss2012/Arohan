import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    unit_id = Column(String(36), ForeignKey("units.id"), nullable=True)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=True)
    faculty_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    academic_year_id = Column(String(36), ForeignKey("academic_years.id"), nullable=True)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=True)
    division_id = Column(String(36), ForeignKey("divisions.id"), nullable=True)
    assignment_type = Column(String(50), default="INDIVIDUAL") # INDIVIDUAL, GROUP, PRACTICAL
    difficulty = Column(String(20), default="MEDIUM")
    total_marks = Column(Float, default=100.0)
    passing_marks = Column(Float, default=40.0)
    start_date = Column(DateTime(timezone=True), default=get_utc_now)
    due_date = Column(DateTime(timezone=True), nullable=False)
    late_submission_allowed = Column(Boolean, default=True)
    late_penalty_percentage = Column(Float, default=10.0)
    max_attempts = Column(Integer, default=1)
    status = Column(String(50), default="PUBLISHED") # DRAFT, PUBLISHED, CLOSED, ARCHIVED
    file_id = Column(String(36), ForeignKey("files.id"), nullable=True) # Attached Question Paper/Instructions Doc
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    published_at = Column(DateTime(timezone=True), default=get_utc_now)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    submissions = relationship("AssignmentSubmission", back_populates="assignment", cascade="all, delete-orphan")

class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    assignment_id = Column(String(36), ForeignKey("assignments.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    attempt_number = Column(Integer, default=1)
    submitted_at = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="SUBMITTED") # DRAFT, SUBMITTED, LATE, UNDER_REVIEW, EVALUATED, RETURNED, RESUBMISSION_REQUESTED
    submission_text = Column(Text, nullable=True)
    total_marks = Column(Float, default=100.0)
    marks_obtained = Column(Float, nullable=True)
    percentage = Column(Float, nullable=True)
    grade = Column(String(10), nullable=True)
    faculty_feedback = Column(Text, nullable=True)
    evaluated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    evaluated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    
    assignment = relationship("Assignment", back_populates="submissions")
    submission_files = relationship("SubmissionFile", back_populates="submission", cascade="all, delete-orphan")
    evaluation = relationship("AssignmentEvaluation", uselist=False, back_populates="submission", cascade="all, delete-orphan")

class SubmissionFile(Base):
    __tablename__ = "submission_files"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("assignment_submissions.id"), nullable=False)
    file_id = Column(String(36), ForeignKey("files.id"), nullable=False)
    file_type = Column(String(50), default="SOLUTION")
    uploaded_at = Column(DateTime(timezone=True), default=get_utc_now)
    version = Column(Integer, default=1)
    status = Column(String(50), default="ACTIVE")
    
    submission = relationship("AssignmentSubmission", back_populates="submission_files")

class Rubric(Base):
    __tablename__ = "rubrics"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    total_marks = Column(Float, default=100.0)
    created_by = Column(String(36), nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    criteria = relationship("RubricCriterion", back_populates="rubric", cascade="all, delete-orphan")

class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    rubric_id = Column(String(36), ForeignKey("rubrics.id"), nullable=False)
    criterion_name = Column(String(100), nullable=False) # e.g. "UI Design", "Backend Architecture"
    max_marks = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    description = Column(Text, nullable=True)
    
    rubric = relationship("Rubric", back_populates="criteria")

class AssignmentEvaluation(Base):
    __tablename__ = "assignment_evaluations"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("assignment_submissions.id"), nullable=False)
    faculty_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rubric_id = Column(String(36), ForeignKey("rubrics.id"), nullable=True)
    marks_obtained = Column(Float, nullable=False)
    percentage = Column(Float, nullable=False)
    grade = Column(String(10), nullable=False)
    feedback = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)
    improvements = Column(Text, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=get_utc_now)
    published_at = Column(DateTime(timezone=True), default=get_utc_now)
    status = Column(String(50), default="PUBLISHED")
    
    submission = relationship("AssignmentSubmission", back_populates="evaluation")
