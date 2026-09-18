import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Program(Base):
    __tablename__ = "programs"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False)
    name = Column(String(100), nullable=False) # e.g. BCA, MCA
    duration_years = Column(Integer, default=3)
    
    department = relationship("Department", back_populates="programs")
    semesters = relationship("Semester", back_populates="program")

class Semester(Base):
    __tablename__ = "semesters"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    program_id = Column(String(36), ForeignKey("programs.id"), nullable=False)
    semester_number = Column(Integer, nullable=False)
    academic_year = Column(String(50), default="2025-2026")
    
    program = relationship("Program", back_populates="semesters")
    subjects = relationship("Subject", back_populates="semester")

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    semester_id = Column(String(36), ForeignKey("semesters.id"), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False)
    credits = Column(Integer, default=4)
    
    semester = relationship("Semester", back_populates="subjects")
    units = relationship("Unit", back_populates="subject")

class Unit(Base):
    __tablename__ = "units"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    
    subject = relationship("Subject", back_populates="units")
    topics = relationship("Topic", back_populates="unit")

class Topic(Base):
    __tablename__ = "topics"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    unit_id = Column(String(36), ForeignKey("units.id"), nullable=False)
    title = Column(String(200), nullable=False)
    learning_objective = Column(Text, nullable=True)
    sequence_order = Column(Integer, default=1)
    
    unit = relationship("Unit", back_populates="topics")
    resources = relationship("Resource", back_populates="topic")

class Resource(Base):
    __tablename__ = "resources"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    title = Column(String(200), nullable=False)
    resource_type = Column(String(50), default="NOTES") # NOTES, PDF, VIDEO, CODE
    file_url = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now)
    
    topic = relationship("Topic", back_populates="resources")

class StudentTopicProgress(Base):
    __tablename__ = "student_topic_progress"
    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    topic_id = Column(String(36), ForeignKey("topics.id"), nullable=False)
    status = Column(String(50), default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, COMPLETED
    time_spent_seconds = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now)
