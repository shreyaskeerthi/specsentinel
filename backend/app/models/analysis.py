"""AnalysisResult model - structured extraction and risk flags for a Document."""

import uuid
from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class AnalysisResult(Base, TimestampMixin):
    """
    AnalysisResult model - stores structured extraction and risk report.
    JSON fields hold the SpecExtraction and RiskReport data.
    """

    __tablename__ = "analysis_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Extracted raw text (can be large)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured extraction data (stored as JSON)
    # Contains: insurance, bonding, warranty, liquidated_damages, testing, commissioning, etc.
    extraction_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Risk report (stored as JSON)
    # Contains: overall_summary, flags: [{type, severity, description}]
    risk_report: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Division-specific extractions (stored as JSON)
    # Contains: div22, div23, div26, etc.
    division_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Chunk metadata for source attribution (stored as JSON)
    # Contains: [{chunk_id, page, text, start_index, end_index, division, section}]
    chunks_data: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), unique=True, nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document", back_populates="analysis"
    )

    def __repr__(self) -> str:
        return f"<AnalysisResult for document={self.document_id}>"
