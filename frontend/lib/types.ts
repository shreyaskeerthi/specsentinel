/**
 * TypeScript types for API data structures.
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "owner" | "admin" | "estimator" | "viewer";
  is_active: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  client_name: string | null;
  description: string | null;
  bid_due_date: string | null;
  status: "active" | "won" | "lost" | "no_bid" | "archived";
  organization_id: string;
  created_at: string;
  updated_at: string;
  documents?: DocumentBrief[];
}

export interface ProjectListItem {
  id: string;
  name: string;
  client_name: string | null;
  bid_due_date: string | null;
  status: string;
  document_count: number;
  last_analysis_date: string | null;
  created_at: string;
}

export interface DocumentBrief {
  id: string;
  original_filename: string;
  status: "pending" | "processing" | "completed" | "failed";
  page_count: number | null;
  created_at: string;
  has_analysis: boolean;
  risk_count: number;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  page_count: number | null;
  project_id: string;
  created_at: string;
  updated_at: string;
}

export interface SpecLocation {
  section: string | null;
  page: number | null;
  chunk_id: string | null;
}

export type Responsibility = "gc" | "mechanical" | "electrical" | "plumbing" | "controls" | "owner" | "shared" | "unknown";
export type RiskStatus = "open" | "acknowledged" | "included_in_bid" | "will_clarify" | "accepted";
export type CostImpactType = "none" | "fixed" | "percentage" | "hourly" | "uncapped";
export type GoNoGoRecommendation = "proceed" | "proceed_with_contingency" | "caution" | "do_not_bid";

export interface CostImpact {
  type: CostImpactType;
  min_dollars: number | null;
  max_dollars: number | null;
  percentage_of_contract: number | null;
  description: string | null;
}

export interface RiskFlag {
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
  source_text: string | null;
  source_quote?: string | null;  // Short direct quote from spec
  spec_location?: SpecLocation | string | null;  // Structured location or legacy string
  impact?: string[] | null;
  recommended_action?: string[] | null;
  bid_cost_impact?: string | null;  // Legacy field
  cost_impact?: CostImpact | null;  // New structured cost impact
  responsibility?: Responsibility;  // Who bears this risk
  status?: RiskStatus;  // User-set status for tracking
  risk_id?: string | null;
  category?: string | null;
}

export interface ProjectSummary {
  project_name: string | null;
  location: string | null;
  project_type: string | null;
  scope_description: string | null;
  schedule_constraints: string | null;
  occupied_building?: boolean | null;
  union_required?: boolean | null;
}

export interface ChecklistItem {
  item: string;
  category?: string | null;
  estimated_cost?: string | null;
  priority?: "high" | "medium" | "low" | null;
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
  overall_risk_level: "low" | "medium" | "high" | "critical";
  overall_summary: string;
  flags: RiskFlag[];
  total_flags: number;
  high_severity_count: number;
  project_summary?: ProjectSummary | null;
  estimator_checklist?: EstimatorChecklist | null;
  go_no_go?: GoNoGo | null;
  financial_exposure?: FinancialExposure | null;
}

export interface SpecExtraction {
  insurance_requirements: string | null;
  bonding_requirements: string | null;
  warranty_requirements: string | null;
  liquidated_damages: string | null;
  testing_requirements: string | null;
  commissioning_requirements: string | null;
  submittals_summary: string | null;
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

export interface TextChunk {
  chunk_id: string;
  page: number;
  text: string;
  start_index: number;
  end_index: number;
  division: string | null;
  section: string | null;
}

export interface AnalysisResult {
  id: string;
  document_id: string;
  extraction: SpecExtraction;
  risk_report: RiskReport;
  division_data: DivisionData | null;
  chunks?: TextChunk[] | null;  // Document chunks for navigation
  created_at: string;
  updated_at: string;
}

export interface Plan {
  id: string;
  name: string;
  tier: "free" | "pro" | "enterprise";
  price_monthly_cents: number;
  price_yearly_cents: number;
  max_projects: number;
  max_documents_per_month: number;
  max_users: number;
}

export interface Subscription {
  id: string;
  status: "active" | "past_due" | "canceled" | "trialing";
  plan: Plan | null;
  current_period_start: string | null;
  current_period_end: string | null;
  documents_analyzed_this_month: number;
  projects_count: number;
}

export interface UsageStats {
  documents_analyzed_this_month: number;
  documents_limit: number;
  projects_count: number;
  projects_limit: number;
  users_count: number;
  users_limit: number;
  plan_tier: string;
}
