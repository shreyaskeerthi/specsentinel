"""Billing and subscription schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.subscription import PlanTier, SubscriptionStatus


class PlanRead(BaseModel):
    """Subscription plan details."""
    id: UUID
    name: str
    tier: PlanTier
    price_monthly_cents: int
    price_yearly_cents: int
    max_projects: int
    max_documents_per_month: int
    max_users: int

    class Config:
        from_attributes = True


class SubscriptionRead(BaseModel):
    """Subscription details for an organization."""
    id: UUID
    status: SubscriptionStatus
    plan: PlanRead | None = None
    current_period_start: datetime | None
    current_period_end: datetime | None
    documents_analyzed_this_month: int
    projects_count: int

    class Config:
        from_attributes = True


class UsageStats(BaseModel):
    """Current usage statistics for an organization."""
    documents_analyzed_this_month: int
    documents_limit: int
    projects_count: int
    projects_limit: int
    users_count: int
    users_limit: int
    plan_tier: PlanTier


class CheckoutRequest(BaseModel):
    """Request to start checkout session."""
    plan_tier: PlanTier
    billing_period: str = "monthly"  # "monthly" or "yearly"


class CheckoutResponse(BaseModel):
    """Response with checkout URL."""
    checkout_url: str
    session_id: str
