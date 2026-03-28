"""Project schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    """Base project fields."""
    name: str
    client_name: str | None = None
    description: str | None = None
    bid_due_date: date | None = None


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: str | None = None
    client_name: str | None = None
    description: str | None = None
    bid_due_date: date | None = None
    status: ProjectStatus | None = None


class ProjectListItem(BaseModel):
    """Schema for project list item (lighter weight)."""
    id: UUID
    name: str
    client_name: str | None
    bid_due_date: date | None
    status: ProjectStatus
    document_count: int = 0
    last_analysis_date: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectRead(ProjectBase):
    """Schema for reading a full project."""
    id: UUID
    status: ProjectStatus
    organization_id: UUID
    created_at: datetime
    updated_at: datetime
    documents: list["DocumentReadBrief"] = []

    class Config:
        from_attributes = True


# Forward reference for circular import
from app.schemas.document import DocumentReadBrief  # noqa: E402

ProjectRead.model_rebuild()
