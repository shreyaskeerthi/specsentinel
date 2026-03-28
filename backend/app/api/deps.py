"""API dependencies for authentication and authorization."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.organization import Organization
from app.models.subscription import Subscription, PlanTier

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def get_current_organization(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Organization:
    """Get the organization of the current user."""
    org = db.query(Organization).filter(
        Organization.id == current_user.organization_id
    ).first()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


def check_usage_limits(
    db: Annotated[Session, Depends(get_db)],
    organization: Annotated[Organization, Depends(get_current_organization)],
) -> Organization:
    """Check if organization is within usage limits."""
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    if not subscription or not subscription.plan:
        # No subscription - use free tier limits
        max_docs = 10
        max_projects = 3
    else:
        max_docs = subscription.plan.max_documents_per_month
        max_projects = subscription.plan.max_projects

    # Check limits (0 means unlimited)
    if max_docs > 0 and subscription and subscription.documents_analyzed_this_month >= max_docs:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Monthly document analysis limit reached. Please upgrade your plan.",
        )

    if max_projects > 0 and subscription and subscription.projects_count >= max_projects:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Project limit reached. Please upgrade your plan.",
        )

    return organization


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_active_user)]
CurrentOrg = Annotated[Organization, Depends(get_current_organization)]
DbSession = Annotated[Session, Depends(get_db)]
