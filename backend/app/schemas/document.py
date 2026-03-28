"""Document schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentBase(BaseModel):
    """Base document fields."""
    original_filename: str


class DocumentReadBrief(BaseModel):
    """Brief document info for project list."""
    id: UUID
    original_filename: str
    status: DocumentStatus
    page_count: int | None
    created_at: datetime
    has_analysis: bool = False
    risk_count: int = 0

    class Config:
        from_attributes = True


class DocumentRead(DocumentBase):
    """Full document read schema."""
    id: UUID
    filename: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    page_count: int | None
    project_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response after document upload and analysis."""
    document: DocumentRead
    analysis: "AnalysisResultRead | None" = None


# Forward reference
from app.schemas.analysis import AnalysisResultRead  # noqa: E402

DocumentUploadResponse.model_rebuild()
