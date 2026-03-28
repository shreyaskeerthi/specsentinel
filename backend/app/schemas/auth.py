"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """Registration request schema - creates org + first user."""
    organization_name: str
    full_name: str
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    sub: str | None = None
