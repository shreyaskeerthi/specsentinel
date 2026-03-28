"""Analysis endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, CurrentOrg
from app.models.document import Document
from app.models.project import Project
from app.models.analysis import AnalysisResult
from app.schemas.analysis import AnalysisResultRead, SpecExtraction, RiskReport, DivisionData

router = APIRouter()


@router.get("/{document_id}", response_model=AnalysisResultRead)
def get_analysis(
    *,
    db: DbSession,
    organization: CurrentOrg,
    document_id: UUID,
) -> AnalysisResultRead:
    """Get analysis result for a specific document."""
    # Verify document belongs to organization
    document = db.query(Document).join(Project).filter(
        Document.id == document_id,
        Project.organization_id == organization.id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.document_id == document_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found for this document",
        )

    return AnalysisResultRead(
        id=analysis.id,
        document_id=analysis.document_id,
        extraction=SpecExtraction(**analysis.extraction_data),
        risk_report=RiskReport(**analysis.risk_report),
        division_data=DivisionData(**analysis.division_data) if analysis.division_data else None,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
    )


@router.get("/project/{project_id}", response_model=list[AnalysisResultRead])
def get_project_analyses(
    *,
    db: DbSession,
    organization: CurrentOrg,
    project_id: UUID,
) -> list[AnalysisResultRead]:
    """Get all analyses for a project."""
    # Verify project belongs to organization
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get all documents with analyses
    documents = db.query(Document).options(
        joinedload(Document.analysis)
    ).filter(
        Document.project_id == project_id
    ).all()

    results = []
    for doc in documents:
        if doc.analysis:
            results.append(AnalysisResultRead(
                id=doc.analysis.id,
                document_id=doc.analysis.document_id,
                extraction=SpecExtraction(**doc.analysis.extraction_data),
                risk_report=RiskReport(**doc.analysis.risk_report),
                division_data=DivisionData(**doc.analysis.division_data) if doc.analysis.division_data else None,
                created_at=doc.analysis.created_at,
                updated_at=doc.analysis.updated_at,
            ))

    return results
