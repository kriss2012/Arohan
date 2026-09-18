from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class RecommendationOut(BaseModel):
    id: str
    skill_id: str
    skill_name: str
    category: str
    action_type: str
    title: str
    evidence_summary: str
    mathematical_rationale: Optional[str] = None
    why_endpoint: str
    is_completed: bool

class SkillCompetencyOut(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    mastery_probability: float
    confidence_score: float
    evidence_count: int
    status_label: str # Novice, Developing, Proficient, Mastered, Insufficient Evidence

class EvidenceDrawerOut(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    mastery_probability: float
    confidence_score: float
    evidence_count: int
    correct_count: int
    incorrect_count: int
    gap_score: float
    recommendation_logic: str
    recent_evidence_events: List[Dict[str, Any]] = []

class InterventionCreate(BaseModel):
    student_id: str
    skill_id: str
    intervention_type: str = "REMEDIAL_PRACTICE"
    notes: str

class InterventionOut(BaseModel):
    id: str
    student_id: str
    student_name: str
    faculty_id: str
    faculty_name: str
    skill_name: str
    intervention_type: str
    notes: str
    status: str
    created_at: datetime
