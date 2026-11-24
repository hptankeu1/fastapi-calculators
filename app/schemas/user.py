from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$",
                          examples=["alice"])
    email: EmailStr = Field(examples=["alice@example.com"])
    password: str = Field(min_length=8, max_length=128, examples=["Secret123"])

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class UserLogin(BaseModel):
    """Log in with either the username or the email."""
    username_or_email: str = Field(min_length=3, examples=["alice"])
    password: str = Field(min_length=1, examples=["Secret123"])


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
