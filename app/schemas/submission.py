from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.submission import SubmissionStatus
from app.schemas.evaluation import EvaluationResponse


class SubmissionCreate(BaseModel):
    raw_text: str


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    status: SubmissionStatus
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)



class SubmissionDetailResponse(SubmissionResponse):
    raw_text: str
    evaluation: Optional[EvaluationResponse] = None
