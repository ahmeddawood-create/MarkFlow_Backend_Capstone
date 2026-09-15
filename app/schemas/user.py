from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.user import UserRole

try:
    import email_validator
    from pydantic import EmailStr
except ImportError:
    from typing import Annotated
    from pydantic import StringConstraints
    EmailStr = Annotated[str, StringConstraints(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    role: UserRole = UserRole.STUDENT


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

