"""Analysis schemas - spec extraction and risk report."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class RiskSeverity(str, Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    """Types of identified risks."""
    WARRANTY = "warranty"
    PENALTY = "penalty"
    BONDING = "bonding"
    INSURANCE = "insurance"
    TESTING = "testing"
    COMMISSIONING = "commissioning"
    SCHEDULE = "schedule"
    SCOPE = "scope"
    OTHER = "other"


class Responsibility(str, Enum):
    """Who is responsible for addressing the risk."""
    GC = "gc"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    CONTROLS = "controls"
    OWNER = "owner"
    SHARED = "shared"
    UNKNOWN = "unknown"


class GoNoGoRecommendation(str, Enum):
    """Bid go/no-go recommendation."""
    PROCEED = "proceed"
    PROCEED_WITH_CONTINGENCY = "proceed_with_contingency"
    CAUTION = "caution"
    DO_NOT_BID = "do_not_bid"


class RiskStatus(str, Enum):
    """Status of risk item handling."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INCLUDED_IN_BID = "included_in_bid"
    WILL_CLARIFY = "will_clarify"
    ACCEPTED = "accepted"


class CostImpactType(str, Enum):
    """Type of cost impact."""
    NONE = "none"
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    HOURLY = "hourly"
    UNCAPPED = "uncapped"


class SpecExtraction(BaseModel):
    """Structured extraction from spec document."""
    insurance_requirements: str | None = None
    bonding_requirements: str | None = None
    warranty_requirements: str | None = None
    liquidated_damages: str | None = None
    testing_requirements: str | None = None
    commissioning_requirements: str | None = None
    submittals_summary: str | None = None
    div22_requirements: str | None = None  # Plumbing
    div23_requirements: str | None = None  # HVAC
    div26_requirements: str | None = None  # Electrical


class SpecLocation(BaseModel):
    """Location in the spec document where a risk was found."""
    section: str | None = None  # e.g., "23 05 93"
    page: int | None = None  # PDF page number (1-based)
    chunk_id: str | None = None  # Internal chunk identifier for navigation


class CostImpact(BaseModel):
    """Detailed cost impact for a risk."""
    type: CostImpactType = CostImpactType.NONE
    min_dollars: int | None = None  # e.g., 5000
    max_dollars: int | None = None  # e.g., 25000
    percentage_of_contract: float | None = None  # e.g., 2.5
    description: str | None = None  # e.g., "$5,000-$25,000 added cost"


class RiskFlag(BaseModel):
    """Individual risk flag identified in analysis."""
    type: RiskType
    severity: RiskSeverity
    title: str
    description: str
    source_text: str | None = None  # Spec quote that triggered the flag (legacy)
    source_quote: str | None = None  # Short direct quote from spec
    spec_location: SpecLocation | str | None = None  # Structured location or legacy string
    impact: list[str] | None = None  # Impact bullet points
    recommended_action: list[str] | None = None  # Action items
    bid_cost_impact: str | None = None  # Legacy: None/Minimal, Likely $, $$, $$$
    cost_impact: CostImpact | None = None  # New structured cost impact
    responsibility: Responsibility = Responsibility.UNKNOWN  # Who bears this risk
    status: RiskStatus = RiskStatus.OPEN  # User-set status for tracking
    risk_id: str | None = None  # R1, R2, etc.
    category: str | None = None  # Detailed category


class ProjectSummary(BaseModel):
    """Project summary from spec analysis."""
    project_name: str | None = None
    location: str | None = None
    project_type: str | None = None  # school, hospital, commercial, industrial, etc.
    scope_description: str | None = None
    schedule_constraints: str | None = None
    occupied_building: bool | None = None
    union_required: bool | None = None


class ChecklistItem(BaseModel):
    """Single checklist item with category/priority."""
    item: str
    category: str | None = None  # Insurance, Bonds, Schedule, Scope, Other
    estimated_cost: str | None = None  # e.g., "$X-$Y" or "+X%"
    priority: str | None = None  # high, medium, low


class EstimatorChecklist(BaseModel):
    """Checklist items for estimator."""
    must_confirm_before_pricing: list[ChecklistItem | str] = []
    include_in_bid_cost: list[ChecklistItem | str] = []
    clarify_via_rfi: list[ChecklistItem | str] = []


class GoNoGo(BaseModel):
    """Go/No-Go bid recommendation."""
    recommendation: GoNoGoRecommendation = GoNoGoRecommendation.PROCEED
    contingency_percent: float = 0  # Suggested contingency percentage (0-25)
    key_concerns: list[str] = []  # Top 3 concerns
    reasoning: str | None = None  # Explanation of recommendation


class FinancialExposure(BaseModel):
    """Summary of financial exposure from identified risks."""
    total_identified_min: int = 0  # Sum of all min cost impacts
    total_identified_max: int = 0  # Sum of all max cost impacts
    ld_daily_rate: int | None = None  # Liquidated damages per day
    ld_cap: int | None = None  # LD cap if specified
    bond_percentage: float | None = None  # Bond requirement %
    retention_percentage: float | None = None  # Retention %


class RiskReport(BaseModel):
    """Complete risk report for a document."""
    overall_risk_level: RiskSeverity
    overall_summary: str
    flags: list[RiskFlag] = []
    total_flags: int = 0
    high_severity_count: int = 0
    project_summary: ProjectSummary | dict | None = None
    estimator_checklist: EstimatorChecklist | dict | None = None
    go_no_go: GoNoGo | dict | None = None
    financial_exposure: FinancialExposure | dict | None = None


class DivisionData(BaseModel):
    """Division-specific extracted data."""
    div22_plumbing: str | None = None
    div23_hvac: str | None = None
    div26_electrical: str | None = None
    div00_procurement: str | None = None
    div01_general: str | None = None


class TextChunkSchema(BaseModel):
    """Schema for a text chunk from PDF extraction."""
    chunk_id: str
    page: int
    text: str
    start_index: int
    end_index: int
    division: str | None = None
    section: str | None = None


class AnalysisResultRead(BaseModel):
    """Full analysis result response."""
    id: UUID
    document_id: UUID
    extraction: SpecExtraction
    risk_report: RiskReport
    division_data: DivisionData | None = None
    chunks: list[TextChunkSchema] | None = None  # Document chunks for navigation
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
