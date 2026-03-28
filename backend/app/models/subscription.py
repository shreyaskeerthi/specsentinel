"""Subscription models - plan and billing for Organizations."""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    TRIALING = "trialing"


class SubscriptionPlan(Base, TimestampMixin):
    """
    SubscriptionPlan model - defines available plans and their limits.
    """

    __tablename__ = "subscription_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(unique=True, nullable=False)
    price_monthly_cents: Mapped[int] = mapped_column(Integer, default=0)
    price_yearly_cents: Mapped[int] = mapped_column(Integer, default=0)

    # Usage limits
    max_projects: Mapped[int] = mapped_column(Integer, default=3)  # 0 = unlimited
    max_documents_per_month: Mapped[int] = mapped_column(Integer, default=10)  # 0 = unlimited
    max_users: Mapped[int] = mapped_column(Integer, default=1)  # 0 = unlimited

    # Feature flags (JSON or individual columns)
    stripe_price_id_monthly: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_price_id_yearly: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<SubscriptionPlan {self.tier.value}>"


class Subscription(Base, TimestampMixin):
    """
    Subscription model - links an Organization to a plan.
    """

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[SubscriptionStatus] = mapped_column(default=SubscriptionStatus.ACTIVE)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Usage tracking for current period
    documents_analyzed_this_month: Mapped[int] = mapped_column(Integer, default=0)
    projects_count: Mapped[int] = mapped_column(Integer, default=0)

    # Stripe integration (TODO: implement webhooks)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), unique=True, nullable=False
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="subscription"
    )
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")

    def __repr__(self) -> str:
        return f"<Subscription org={self.organization_id} status={self.status.value}>"
