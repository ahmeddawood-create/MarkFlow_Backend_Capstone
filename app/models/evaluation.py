from typing import Optional, Any, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from app.models.submission import Submission


class Evaluation(SQLModel, table=True):
    __tablename__ = "evaluations"

    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: int = Field(foreign_key="submissions.id", unique=True, index=True, nullable=False)
    score_awarded: float = Field(nullable=False)
    max_possible_score: float = Field(default=10.0, nullable=False)
    
    # Granular step-by-step mark scheme breakdown
    # e.g.: [{"step": 1, "awarded": 3.0, "max": 3.0, "notes": "Correct formula applied"}]
    step_breakdown: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    overall_feedback: str = Field(default="", nullable=False)

    # Metrics & Cost Tracking (Hits capstone stretch goal: Measure the 10x)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)
    latency_seconds: float = Field(default=0.0)
    graded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationship
    submission: Optional["Submission"] = Relationship(back_populates="evaluation")
