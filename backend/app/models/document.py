"""Document model - uploaded PDF linked to a Project."""

import uuid
from enum import Enum

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base, TimestampMixin):
    """
    Document model - an uploaded PDF file for analysis.
    Linked to a Project, has an AnalysisResult after processing.
    """

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf")
    status: Mapped[DocumentStatus] = mapped_column(default=DocumentStatus.PENDING)
    page_count: Mapped[int | None] = mapped_column(nullable=True)

    # Foreign keys
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="documents"
    )
    analysis: Mapped["AnalysisResult"] = relationship(  # noqa: F821
        "AnalysisResult", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document {self.original_filename}>"
