"""Analysis schemas — spec extraction, risk report, action board, emails."""

from enum import Enum
from pydantic import BaseModel


# --- Enums ---

class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
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
    GC = "gc"
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    CONTROLS = "controls"
    OWNER = "owner"
    SHARED = "shared"
    UNKNOWN = "unknown"


class GoNoGoRecommendation(str, Enum):
    PROCEED = "proceed"
    PROCEED_WITH_CONTINGENCY = "proceed_with_contingency"
    CAUTION = "caution"
    DO_NOT_BID = "do_not_bid"


class RiskStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INCLUDED_IN_BID = "included_in_bid"
    WILL_CLARIFY = "will_clarify"
    ACCEPTED = "accepted"


class CostImpactType(str, Enum):
    NONE = "none"
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    HOURLY = "hourly"
    UNCAPPED = "uncapped"


class TaskPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(str, Enum):
    TO_CLARIFY = "to_clarify"
    MUST_INCLUDE = "must_include"
    INTERNAL = "internal"


class OwnerType(str, Enum):
    ESTIMATING = "Estimating"
    PM = "PM"
    FINANCE = "Finance"
    OPS = "Ops"


# --- Spec Extraction ---

class SpecExtraction(BaseModel):
    insurance_requirements: str | None = None
    bonding_requirements: str | None = None
    warranty_requirements: str | None = None
    liquidated_damages: str | None = None
    testing_requirements: str | None = None
    commissioning_requirements: str | None = None
    submittals_summary: str | None = None
    closeout_requirements: str | None = None
    schedule_requirements: str | None = None
    div22_requirements: str | None = None
    div23_requirements: str | None = None
    div26_requirements: str | None = None


# --- Risk Report ---

class SpecLocation(BaseModel):
    section: str | None = None
    page: int | None = None
    chunk_id: str | None = None


class CostImpact(BaseModel):
    type: CostImpactType = CostImpactType.NONE
    min_dollars: int | None = None
    max_dollars: int | None = None
    percentage_of_contract: float | None = None
    description: str | None = None


class RiskFlag(BaseModel):
    type: RiskType
    severity: RiskSeverity
    title: str
    description: str
    source_text: str | None = None
    source_quote: str | None = None
    spec_location: SpecLocation | str | None = None
    impact: list[str] | None = None
    recommended_action: list[str] | None = None
    bid_cost_impact: str | None = None
    cost_impact: CostImpact | None = None
    responsibility: Responsibility = Responsibility.UNKNOWN
    status: RiskStatus = RiskStatus.OPEN
    risk_id: str | None = None
    category: str | None = None


class ProjectSummary(BaseModel):
    project_name: str | None = None
    location: str | None = None
    project_type: str | None = None
    scope_description: str | None = None
    schedule_constraints: str | None = None
    occupied_building: bool | None = None
    union_required: bool | None = None


class ChecklistItem(BaseModel):
    item: str
    category: str | None = None
    estimated_cost: str | None = None
    priority: str | None = None


class EstimatorChecklist(BaseModel):
    must_confirm_before_pricing: list[ChecklistItem | str] = []
    include_in_bid_cost: list[ChecklistItem | str] = []
    clarify_via_rfi: list[ChecklistItem | str] = []


class GoNoGo(BaseModel):
    recommendation: GoNoGoRecommendation = GoNoGoRecommendation.PROCEED
    contingency_percent: float = 0
    key_concerns: list[str] = []
    reasoning: str | None = None


class FinancialExposure(BaseModel):
    total_identified_min: int = 0
    total_identified_max: int = 0
    ld_daily_rate: int | None = None
    ld_cap: int | None = None
    bond_percentage: float | None = None
    retention_percentage: float | None = None


class RiskReport(BaseModel):
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
    div22_plumbing: str | None = None
    div23_hvac: str | None = None
    div26_electrical: str | None = None
    div00_procurement: str | None = None
    div01_general: str | None = None


class TextChunkSchema(BaseModel):
    chunk_id: str
    page: int
    text: str
    start_index: int
    end_index: int
    division: str | None = None
    section: str | None = None


# --- Action Board ---

class ActionTask(BaseModel):
    id: str
    title: str
    description: str
    priority: TaskPriority
    category: TaskCategory
    owner_type: OwnerType
    linked_risk_id: str | None = None
    page_reference: int | None = None
    due_date: str | None = None  # ISO date string
    assignee: str | None = None
    status: str = "open"  # open, in_progress, done


class ActionBoard(BaseModel):
    to_clarify: list[ActionTask] = []
    must_include: list[ActionTask] = []
    internal: list[ActionTask] = []


# --- Emails ---

class GeneratedEmail(BaseModel):
    type: str  # "rfi", "internal", "finance"
    subject: str
    recipients: str  # role-based, e.g. "GC / Owner Rep"
    body: str


class EmailSet(BaseModel):
    emails: list[GeneratedEmail] = []


# --- Meeting Notes ---

class MeetingDecision(BaseModel):
    decision: str
    impact: str | None = None
    owner: str | None = None


class MeetingAttendee(BaseModel):
    name: str
    role: str | None = None


class MeetingRiskUpdate(BaseModel):
    title: str
    severity: RiskSeverity
    description: str
    cost_impact_min: int | None = None
    cost_impact_max: int | None = None
    cost_impact_description: str | None = None
    responsibility: str | None = None
    is_new: bool = True
    related_risk_id: str | None = None  # e.g. "R3" — patches existing flag


class MeetingTaskUpdate(BaseModel):
    title: str
    priority: TaskPriority
    category: TaskCategory
    owner_type: OwnerType
    description: str
    due_date: str | None = None
    assignee: str | None = None
    linked_task_id: str | None = None  # if set, patch existing task instead of appending
    new_status: str | None = None       # "open", "in_progress", "done"


class ScheduleEvent(BaseModel):
    title: str
    date: str  # ISO date
    type: str  # "deadline", "milestone", "task", "blackout", "meeting"
    description: str | None = None
    linked_task_id: str | None = None


class MeetingAnalysis(BaseModel):
    summary: str | None = None
    attendees: list[MeetingAttendee] = []
    key_decisions: list[MeetingDecision] = []
    new_risks: list[MeetingRiskUpdate] = []
    updated_tasks: list[MeetingTaskUpdate] = []
    schedule_events: list[ScheduleEvent] = []
    financial_impact_summary: str | None = None
    revised_exposure_min: int | None = None
    revised_exposure_max: int | None = None


# --- Full Analysis Result (in-memory) ---

class AnalysisResult(BaseModel):
    id: str
    filename: str
    page_count: int
    extraction: SpecExtraction
    risk_report: RiskReport
    division_data: DivisionData | None = None
    action_board: ActionBoard | None = None
    chunks: list[TextChunkSchema] | None = None
