from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.rubric import RubricStepCreate, RubricStepResponse


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    total_marks: float
    rubric_steps: List[RubricStepCreate]


class AssignmentResponse(BaseModel):
    id: int
    tutor_id: int
    title: str
    description: str
    total_marks: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class AssignmentDetailResponse(AssignmentResponse):
    rubric_steps: List[RubricStepResponse] = []
