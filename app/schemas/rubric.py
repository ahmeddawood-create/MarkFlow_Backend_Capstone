from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class RubricStepCreate(BaseModel):
    step_number: int
    description: str
    max_marks: float
    required_keywords: Optional[List[str]] = []
    deduction_rules: Optional[List[str]] = []


class RubricStepResponse(BaseModel):
    id: int
    assignment_id: int
    step_number: int
    description: str
    max_marks: float
    required_keywords: List[str]
    deduction_rules: List[str]

    model_config = ConfigDict(from_attributes=True)

