from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.rubric import RubricStep
    from app.models.submission import Submission


class Assignment(SQLModel, table=True):
    __tablename__ = "assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    tutor_id: int = Field(foreign_key="users.id", index=True, nullable=False)
    title: str = Field(nullable=False)
    description: str = Field(default="")
    total_marks: float = Field(default=10.0, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    tutor: Optional["User"] = Relationship(back_populates="assignments")
    rubric_steps: List["RubricStep"] = Relationship(
        back_populates="assignment",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    submissions: List["Submission"] = Relationship(
        back_populates="assignment",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
