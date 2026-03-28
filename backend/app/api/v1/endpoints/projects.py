"""Project endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession, CurrentUser, CurrentOrg
from app.models.project import Project
from app.models.document import Document
from app.models.subscription import Subscription
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, ProjectListItem

router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    *,
    db: DbSession,
    organization: CurrentOrg,
    current_user: CurrentUser,
    data: ProjectCreate,
) -> Project:
    """Create a new project for the current organization."""
    # Check project limit
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    if subscription and subscription.plan:
        max_projects = subscription.plan.max_projects
        if max_projects > 0 and subscription.projects_count >= max_projects:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Project limit ({max_projects}) reached. Please upgrade your plan.",
            )

    project = Project(
        name=data.name,
        client_name=data.client_name,
        description=data.description,
        bid_due_date=data.bid_due_date,
        organization_id=organization.id,
    )
    db.add(project)

    # Update project count
    if subscription:
        subscription.projects_count += 1

    db.commit()
    db.refresh(project)

    return project


@router.get("/", response_model=list[ProjectListItem])
def list_projects(
    db: DbSession,
    organization: CurrentOrg,
    skip: int = 0,
    limit: int = 50,
) -> list[dict]:
    """List all projects for the current organization."""
    projects = db.query(Project).filter(
        Project.organization_id == organization.id
    ).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for project in projects:
        # Get document count and last analysis date
        docs = db.query(Document).filter(Document.project_id == project.id).all()
        doc_count = len(docs)

        last_analysis_date = None
        for doc in docs:
            if doc.analysis and doc.analysis.created_at:
                if last_analysis_date is None or doc.analysis.created_at > last_analysis_date:
                    last_analysis_date = doc.analysis.created_at

        result.append({
            "id": project.id,
            "name": project.name,
            "client_name": project.client_name,
            "bid_due_date": project.bid_due_date,
            "status": project.status,
            "document_count": doc_count,
            "last_analysis_date": last_analysis_date,
            "created_at": project.created_at,
        })

    return result


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    *,
    db: DbSession,
    organization: CurrentOrg,
    project_id: UUID,
) -> Project:
    """Get a specific project by ID."""
    project = db.query(Project).options(
        joinedload(Project.documents)
    ).filter(
        Project.id == project_id,
        Project.organization_id == organization.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    *,
    db: DbSession,
    organization: CurrentOrg,
    project_id: UUID,
    data: ProjectUpdate,
) -> Project:
    """Update a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    *,
    db: DbSession,
    organization: CurrentOrg,
    project_id: UUID,
):
    """Delete a project and all associated documents."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == organization.id,
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Update project count
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()
    if subscription and subscription.projects_count > 0:
        subscription.projects_count -= 1

    db.delete(project)
    db.commit()
