import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Question(Base):
    __tablename__ = "mcat_questions"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    skill_id = Column(String(36), nullable=False)
    category = Column(String(100), nullable=False) # QUANTITATIVE, LOGICAL, VERBAL, DATA_INTERPRETATION
    subcategory = Column(String(100), nullable=False) # e.g. Percentages, Syllogisms
    difficulty = Column(Float, default=0.5) # 0.0 to 1.0
    question_type = Column(String(50), default="MCQ")
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    status = Column(String(50), default="APPROVED") # DRAFT, AI_GENERATED, FACULTY_REVIEW, APPROVED, RETIRED
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")

class QuestionOption(Base):
    __tablename__ = "mcat_question_options"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    question_id = Column(String(36), ForeignKey("mcat_questions.id"), nullable=False)
    option_key = Column(String(10), nullable=False) # A, B, C, D
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    
    question = relationship("Question", back_populates="options")

class MCATBlueprint(Base):
    __tablename__ = "mcat_blueprints"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    total_questions = Column(Integer, default=20)
    time_limit_minutes = Column(Integer, default=30)
    # JSON string containing category and difficulty distributions
    distribution_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    exams = relationship("MCATExam", back_populates="blueprint")

class MCATExam(Base):
    __tablename__ = "mcat_exams"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    blueprint_id = Column(String(36), ForeignKey("mcat_blueprints.id"), nullable=False)
    title = Column(String(200), nullable=False)
    exam_code = Column(String(50), unique=True, nullable=False)
    mode = Column(String(50), default="DIAGNOSTIC") # DIAGNOSTIC, PRACTICE, MOCK_PLACEMENT
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    blueprint = relationship("MCATBlueprint", back_populates="exams")
    attempts = relationship("MCATAttempt", back_populates="exam")

class MCATAttempt(Base):
    __tablename__ = "mcat_attempts"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    exam_id = Column(String(36), ForeignKey("mcat_exams.id"), nullable=False)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="CREATED")
    # 11 States: CREATED, AUTHORIZED, STARTED, PAUSED, INTERRUPTED, RESUMED, SUBMITTED, AUTO_EVALUATED, UNDER_REVIEW, FINALIZED, CANCELLED
    started_at = Column(DateTime(timezone=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    remaining_seconds = Column(Integer, default=1800)
    score_raw = Column(Float, default=0.0)
    score_percentage = Column(Float, default=0.0)
    total_correct = Column(Integer, default=0)
    total_incorrect = Column(Integer, default=0)
    total_unanswered = Column(Integer, default=0)
    category_scores_json = Column(Text, nullable=True)
    integrity_signal_count = Column(Integer, default=0)
    
    exam = relationship("MCATExam", back_populates="attempts")
    responses = relationship("MCATResponse", back_populates="attempt", cascade="all, delete-orphan")
    integrity_events = relationship("MCATIntegrityEvent", back_populates="attempt", cascade="all, delete-orphan")

class MCATResponse(Base):
    __tablename__ = "mcat_responses"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("mcat_attempts.id"), nullable=False)
    question_id = Column(String(36), ForeignKey("mcat_questions.id"), nullable=False)
    selected_option_id = Column(String(36), nullable=True)
    is_marked_for_review = Column(Boolean, default=False)
    response_time_seconds = Column(Float, default=0.0)
    is_correct = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    attempt = relationship("MCATAttempt", back_populates="responses")

class MCATIntegrityEvent(Base):
    __tablename__ = "mcat_integrity_events"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    attempt_id = Column(String(36), ForeignKey("mcat_attempts.id"), nullable=False)
    event_type = Column(String(50), nullable=False) # FOCUS_LOST, CLIPBOARD_COPY, FULLSCREEN_EXIT, ANOMALY_TIME
    severity = Column(String(20), default="LOW") # LOW, MEDIUM, HIGH
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=get_utc_now)
    
    attempt = relationship("MCATAttempt", back_populates="integrity_events")
