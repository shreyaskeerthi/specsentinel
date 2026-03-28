"""Billing and subscription endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import DbSession, CurrentOrg, CurrentUser
from app.models.subscription import Subscription, SubscriptionPlan, PlanTier
from app.models.user import User
from app.schemas.billing import PlanRead, SubscriptionRead, UsageStats, CheckoutRequest, CheckoutResponse

router = APIRouter()


@router.get("/plans", response_model=list[PlanRead])
def list_plans(db: DbSession) -> list[SubscriptionPlan]:
    """List all available subscription plans."""
    plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly_cents).all()

    # If no plans exist, create default ones
    if not plans:
        default_plans = [
            SubscriptionPlan(
                name="Free",
                tier=PlanTier.FREE,
                price_monthly_cents=0,
                price_yearly_cents=0,
                max_projects=3,
                max_documents_per_month=10,
                max_users=2,
            ),
            SubscriptionPlan(
                name="Pro",
                tier=PlanTier.PRO,
                price_monthly_cents=4900,  # $49/month
                price_yearly_cents=47000,  # $470/year
                max_projects=20,
                max_documents_per_month=100,
                max_users=10,
            ),
            SubscriptionPlan(
                name="Enterprise",
                tier=PlanTier.ENTERPRISE,
                price_monthly_cents=19900,  # $199/month
                price_yearly_cents=199000,  # $1990/year
                max_projects=0,  # unlimited
                max_documents_per_month=0,  # unlimited
                max_users=0,  # unlimited
            ),
        ]
        for plan in default_plans:
            db.add(plan)
        db.commit()
        plans = db.query(SubscriptionPlan).order_by(SubscriptionPlan.price_monthly_cents).all()

    return plans


@router.get("/subscription", response_model=SubscriptionRead)
def get_subscription(
    db: DbSession,
    organization: CurrentOrg,
) -> Subscription:
    """Get current organization's subscription."""
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found",
        )

    return subscription


@router.get("/usage", response_model=UsageStats)
def get_usage(
    db: DbSession,
    organization: CurrentOrg,
) -> UsageStats:
    """Get current usage statistics for the organization."""
    subscription = db.query(Subscription).filter(
        Subscription.organization_id == organization.id
    ).first()

    # Count users
    users_count = db.query(User).filter(
        User.organization_id == organization.id
    ).count()

    if subscription and subscription.plan:
        return UsageStats(
            documents_analyzed_this_month=subscription.documents_analyzed_this_month,
            documents_limit=subscription.plan.max_documents_per_month,
            projects_count=subscription.projects_count,
            projects_limit=subscription.plan.max_projects,
            users_count=users_count,
            users_limit=subscription.plan.max_users,
            plan_tier=subscription.plan.tier,
        )
    else:
        # Default free tier stats
        return UsageStats(
            documents_analyzed_this_month=0,
            documents_limit=10,
            projects_count=0,
            projects_limit=3,
            users_count=users_count,
            users_limit=2,
            plan_tier=PlanTier.FREE,
        )


@router.post("/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    *,
    db: DbSession,
    organization: CurrentOrg,
    current_user: CurrentUser,
    data: CheckoutRequest,
) -> CheckoutResponse:
    """
    Create a Stripe checkout session for plan upgrade.
    TODO: Integrate actual Stripe API.
    """
    # Verify user is owner
    from app.models.user import UserRole
    if current_user.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owner can manage billing",
        )

    # Get the requested plan
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.tier == data.plan_tier
    ).first()

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )

    # TODO: Create actual Stripe checkout session
    # For now, return a placeholder
    # In production, this would:
    # 1. Create/get Stripe customer
    # 2. Create checkout session with price_id
    # 3. Return checkout URL

    return CheckoutResponse(
        checkout_url=f"https://checkout.stripe.com/placeholder?plan={data.plan_tier.value}",
        session_id="placeholder_session_id",
    )


@router.post("/webhook")
async def stripe_webhook():
    """
    Stripe webhook endpoint for subscription events.
    TODO: Implement actual webhook handling.
    """
    # TODO: Implement Stripe webhook handling:
    # 1. Verify webhook signature
    # 2. Handle events:
    #    - checkout.session.completed -> activate subscription
    #    - customer.subscription.updated -> update plan
    #    - customer.subscription.deleted -> cancel subscription
    #    - invoice.payment_failed -> mark as past_due
    pass
