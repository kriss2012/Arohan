from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    resource_type: str
    file_url: Optional[str] = None
    content_text: Optional[str] = None

class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    learning_objective: Optional[str] = None
    sequence_order: int
    resources: List[ResourceOut] = []
    status: Optional[str] = "NOT_STARTED"

class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    unit_number: int
    title: str
    topics: List[TopicOut] = []

class SubjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    code: str
    credits: int
    units: List[UnitOut] = []

class ProgressUpdateRequest(BaseModel):
    status: str # NOT_STARTED, IN_PROGRESS, COMPLETED
    time_spent_seconds: int = 0
