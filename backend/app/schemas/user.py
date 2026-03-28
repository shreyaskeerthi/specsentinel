"""User schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user fields."""
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str
    role: UserRole = UserRole.ESTIMATOR


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    full_name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    """Schema for reading a user."""
    id: UUID
    role: UserRole
    is_active: bool
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
