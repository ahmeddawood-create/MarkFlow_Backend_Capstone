from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.assignment import Assignment
    from app.models.submission import Submission


class UserRole(str, Enum):
    TUTOR = "TUTOR"
    STUDENT = "STUDENT"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(default="")
    role: UserRole = Field(default=UserRole.STUDENT, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments: List["Assignment"] = Relationship(back_populates="tutor")
    submissions: List["Submission"] = Relationship(back_populates="student")
