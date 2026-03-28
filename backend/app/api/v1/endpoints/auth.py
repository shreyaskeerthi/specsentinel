"""Authentication endpoints."""

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import DbSession, CurrentUser
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionPlan, PlanTier
from app.schemas.auth import Token, UserLogin, UserRegister
from app.schemas.user import UserRead

router = APIRouter()


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(*, db: DbSession, data: UserRegister) -> User:
    """
    Register a new organization with the first user (OWNER role).
    Creates organization, user, and assigns free tier subscription.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    base_slug = slugify(data.organization_name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    organization = Organization(
        name=data.organization_name,
        slug=slug,
    )
    db.add(organization)
    db.flush()  # Get organization ID

    # Create user as OWNER
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole.OWNER,
        organization_id=organization.id,
    )
    db.add(user)

    # Get or create free plan
    free_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.tier == PlanTier.FREE
    ).first()

    if not free_plan:
        # Create free plan if it doesn't exist
        free_plan = SubscriptionPlan(
            name="Free",
            tier=PlanTier.FREE,
            price_monthly_cents=0,
            price_yearly_cents=0,
            max_projects=3,
            max_documents_per_month=10,
            max_users=2,
        )
        db.add(free_plan)
        db.flush()

    # Create subscription for organization
    subscription = Subscription(
        organization_id=organization.id,
        plan_id=free_plan.id,
        current_period_start=datetime.utcnow(),
    )
    db.add(subscription)

    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
def login(
    db: DbSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    OAuth2 compatible login endpoint.
    Returns JWT access token.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(subject=str(user.id))

    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token)
def login_json(*, db: DbSession, data: UserLogin) -> Token:
    """
    JSON-based login endpoint (alternative to OAuth2 form).
    """
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(subject=str(user.id))

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserRead)
def get_me(current_user: CurrentUser) -> User:
    """Get current authenticated user."""
    return current_user
