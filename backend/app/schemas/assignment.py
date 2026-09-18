from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    subject_id: str
    unit_id: Optional[str] = None
    topic_id: Optional[str] = None
    academic_year_id: Optional[str] = None
    semester_id: Optional[str] = None
    division_id: Optional[str] = None
    total_marks: float = 100.0
    passing_marks: float = 40.0
    due_date: datetime

class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    subject_id: str
    faculty_id: str
    total_marks: float
    passing_marks: float
    due_date: datetime
    status: str
    file_id: Optional[str] = None
    published_at: datetime

class SubmissionCreate(BaseModel):
    submission_text: Optional[str] = None

class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    assignment_id: str
    student_id: str
    attempt_number: int
    submitted_at: datetime
    status: str
    submission_text: Optional[str] = None
    total_marks: float
    marks_obtained: Optional[float] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None
    faculty_feedback: Optional[str] = None
    evaluated_at: Optional[datetime] = None

class EvaluationCreate(BaseModel):
    submission_id: Optional[str] = None
    marks_obtained: float
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    improvements: Optional[str] = None
