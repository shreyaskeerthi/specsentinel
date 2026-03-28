"""Organization endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession, CurrentUser, CurrentOrg
from app.models.organization import Organization
from app.models.user import User
from app.schemas.organization import OrganizationRead, OrganizationUpdate
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/current", response_model=OrganizationRead)
def get_current_organization(organization: CurrentOrg) -> Organization:
    """Get the current user's organization."""
    return organization


@router.patch("/current", response_model=OrganizationRead)
def update_organization(
    *,
    db: DbSession,
    organization: CurrentOrg,
    current_user: CurrentUser,
    data: OrganizationUpdate,
) -> Organization:
    """
    Update current organization.
    Only OWNER can update organization details.
    """
    from app.models.user import UserRole

    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can update organization details",
        )

    if data.name is not None:
        organization.name = data.name

    db.commit()
    db.refresh(organization)

    return organization


@router.get("/current/users", response_model=list[UserRead])
def list_organization_users(
    db: DbSession,
    organization: CurrentOrg,
) -> list[User]:
    """List all users in the current organization."""
    users = db.query(User).filter(
        User.organization_id == organization.id
    ).all()

    return users
