/**
 * TypeScript types for SpecSentinel v2 — hackathon demo.
 */

// --- Enums ---

export type RiskSeverity = "low" | "medium" | "high" | "critical";
export type RiskType = "warranty" | "penalty" | "bonding" | "insurance" | "testing" | "commissioning" | "schedule" | "scope" | "other";
export type Responsibility = "gc" | "mechanical" | "electrical" | "plumbing" | "controls" | "owner" | "shared" | "unknown";
export type GoNoGoRecommendation = "proceed" | "proceed_with_contingency" | "caution" | "do_not_bid";
export type CostImpactType = "none" | "fixed" | "percentage" | "hourly" | "uncapped";
export type TaskPriority = "high" | "medium" | "low";
export type TaskCategory = "to_clarify" | "must_include" | "internal";
export type OwnerType = "Estimating" | "PM" | "Finance" | "Ops";

// --- Analysis Types ---

export interface CostImpact {
  type: CostImpactType;
  min_dollars: number | null;
  max_dollars: number | null;
  percentage_of_contract: number | null;
  description: string | null;
}

export interface SpecLocation {
  section: string | null;
  page: number | null;
  chunk_id: string | null;
}

export interface RiskFlag {
  type: RiskType;
  severity: RiskSeverity;
  title: string;
  description: string;
  source_text: string | null;
  source_quote: string | null;
  spec_location: SpecLocation | string | null;
  impact: string[] | null;
  recommended_action: string[] | null;
  bid_cost_impact: string | null;
  cost_impact: CostImpact | null;
  responsibility: Responsibility;
  status: string;
  risk_id: string | null;
  category: string | null;
}

export interface ProjectSummary {
  project_name: string | null;
  location: string | null;
  project_type: string | null;
  scope_description: string | null;
  schedule_constraints: string | null;
  occupied_building: boolean | null;
  union_required: boolean | null;
}

export interface ChecklistItem {
  item: string;
  category?: string | null;
  estimated_cost?: string | null;
  priority?: string | null;
}

export interface EstimatorChecklist {
  must_confirm_before_pricing: (ChecklistItem | string)[];
  include_in_bid_cost: (ChecklistItem | string)[];
  clarify_via_rfi: (ChecklistItem | string)[];
}

export interface GoNoGo {
  recommendation: GoNoGoRecommendation;
  contingency_percent: number;
  key_concerns: string[];
  reasoning: string | null;
}

export interface FinancialExposure {
  total_identified_min: number;
  total_identified_max: number;
  ld_daily_rate: number | null;
  ld_cap: number | null;
  bond_percentage: number | null;
  retention_percentage: number | null;
}

export interface RiskReport {
  overall_risk_level: RiskSeverity;
  overall_summary: string;
  flags: RiskFlag[];
  total_flags: number;
  high_severity_count: number;
  project_summary: ProjectSummary | null;
  estimator_checklist: EstimatorChecklist | null;
  go_no_go: GoNoGo | null;
  financial_exposure: FinancialExposure | null;
}

export interface SpecExtraction {
  insurance_requirements: string | null;
  bonding_requirements: string | null;
  warranty_requirements: string | null;
  liquidated_damages: string | null;
  testing_requirements: string | null;
  commissioning_requirements: string | null;
  submittals_summary: string | null;
  closeout_requirements: string | null;
  schedule_requirements: string | null;
  div22_requirements: string | null;
  div23_requirements: string | null;
  div26_requirements: string | null;
}

export interface DivisionData {
  div22_plumbing: string | null;
  div23_hvac: string | null;
  div26_electrical: string | null;
  div00_procurement: string | null;
  div01_general: string | null;
}

// --- Action Board ---

export interface ActionTask {
  id: string;
  title: string;
  description: string;
  priority: TaskPriority;
  category: TaskCategory;
  owner_type: OwnerType;
  linked_risk_id: string | null;
  page_reference: number | null;
  due_date: string | null;
  assignee: string | null;
  status: string;
}

export interface ActionBoard {
  to_clarify: ActionTask[];
  must_include: ActionTask[];
  internal: ActionTask[];
}

// --- Emails ---

export interface GeneratedEmail {
  type: string;
  subject: string;
  recipients: string;
  body: string;
}

export interface EmailSet {
  emails: GeneratedEmail[];
}

// --- Meeting Notes ---

export interface MeetingDecision {
  decision: string;
  impact: string | null;
  owner: string | null;
}

export interface MeetingRiskUpdate {
  title: string;
  severity: RiskSeverity;
  description: string;
  cost_impact_min: number | null;
  cost_impact_max: number | null;
  cost_impact_description: string | null;
  responsibility: string | null;
  is_new: boolean;
}

export interface MeetingTaskUpdate {
  title: string;
  priority: TaskPriority;
  category: TaskCategory;
  owner_type: OwnerType;
  description: string;
  due_date: string | null;
  assignee: string | null;
}

export interface ScheduleEvent {
  title: string;
  date: string;
  type: "deadline" | "milestone" | "task" | "blackout" | "meeting";
  description: string | null;
  linked_task_id: string | null;
}

export interface MeetingAnalysis {
  key_decisions: MeetingDecision[];
  new_risks: MeetingRiskUpdate[];
  updated_tasks: MeetingTaskUpdate[];
  schedule_events: ScheduleEvent[];
  financial_impact_summary: string | null;
  revised_exposure_min: number | null;
  revised_exposure_max: number | null;
}

// --- Full Analysis Result ---

export interface AnalysisResult {
  id: string;
  filename: string;
  page_count: number;
  extraction: SpecExtraction;
  risk_report: RiskReport;
  division_data: DivisionData | null;
  action_board: ActionBoard | null;
  chunks: any[] | null;
}
