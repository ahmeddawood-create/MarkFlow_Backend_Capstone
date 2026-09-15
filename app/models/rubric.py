from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:
    from app.models.assignment import Assignment


class RubricStep(SQLModel, table=True):
    __tablename__ = "rubric_steps"

    id: Optional[int] = Field(default=None, primary_key=True)
    assignment_id: int = Field(foreign_key="assignments.id", index=True, nullable=False)
    step_number: int = Field(nullable=False)
    description: str = Field(nullable=False)
    max_marks: float = Field(default=1.0, nullable=False)
    
    # Store JSON arrays of required terms/rules
    required_keywords: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    deduction_rules: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Relationship
    assignment: Optional["Assignment"] = Relationship(back_populates="rubric_steps")
