from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class QuestionOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    option_key: str
    option_text: str

class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category: str
    subcategory: str
    difficulty: float
    question_type: str
    question_text: str
    options: List[QuestionOptionOut] = []

class QuestionWithAnswerOut(QuestionOut):
    explanation: Optional[str] = None
    correct_option_id: Optional[str] = None

class ExamSummaryOut(BaseModel):
    id: str
    title: str
    exam_code: str
    mode: str
    total_questions: int
    time_limit_minutes: int
    is_published: bool

class AttemptStartRequest(BaseModel):
    exam_id: str

class ResponseSaveRequest(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None
    is_marked_for_review: bool = False
    response_time_seconds: float = 0.0

class IntegrityEventCreate(BaseModel):
    event_type: str # FOCUS_LOST, CLIPBOARD_COPY, FULLSCREEN_EXIT, ANOMALY_TIME
    severity: str = "LOW"
    details: Optional[Dict[str, Any]] = None

class AttemptResponseOut(BaseModel):
    question_id: str
    selected_option_id: Optional[str] = None
    is_marked_for_review: bool = False

class AttemptOut(BaseModel):
    id: str
    exam_id: str
    exam_title: str
    status: str
    remaining_seconds: int
    total_questions: int
    questions: List[QuestionOut] = []
    saved_responses: List[AttemptResponseOut] = []

class ScoreResultOut(BaseModel):
    attempt_id: str
    status: str
    score_raw: float
    score_percentage: float
    total_correct: int
    total_incorrect: int
    total_unanswered: int
    category_scores: Dict[str, float] = {}
    integrity_signal_count: int
