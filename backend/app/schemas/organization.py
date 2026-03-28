"""Organization schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """Base organization fields."""
    name: str


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    name: str | None = None


class OrganizationRead(OrganizationBase):
    """Schema for reading an organization."""
    id: UUID
    slug: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
