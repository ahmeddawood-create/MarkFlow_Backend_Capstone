from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.assignment import Assignment
    from app.models.evaluation import Evaluation


class SubmissionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    GRADED = "GRADED"
    FAILED = "FAILED"


class Submission(SQLModel, table=True):
    __tablename__ = "submissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(foreign_key="assignments.id", index=True, nullable=False)
    student_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    raw_text: str = Field(nullable=False)
    status: SubmissionStatus = Field(default=SubmissionStatus.SUBMITTED, nullable=False)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    assignment: Optional["Assignment"] = Relationship(back_populates="submissions")
    student: Optional["User"] = Relationship(back_populates="submissions")
    evaluation: Optional["Evaluation"] = Relationship(
        back_populates="submission",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )
