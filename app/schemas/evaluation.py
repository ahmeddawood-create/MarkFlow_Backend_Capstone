from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime


class StepScore(BaseModel):
    step: int
    awarded: float
    max: float
    notes: str


class EvaluationResponse(BaseModel):
    id: int
    submission_id: int
    score_awarded: float
    max_possible_score: float
    step_breakdown: List[Dict[str, Any]]
    overall_feedback: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    latency_seconds: float
    graded_at: datetime

    model_config = ConfigDict(from_attributes=True)

