/**
 * Analysis summary component showing extraction and risk report.
 */

import React, { useState } from "react";
import type {
  AnalysisResult, RiskFlag, EstimatorChecklist, ProjectSummary, SpecLocation,
  GoNoGo, FinancialExposure, Responsibility, RiskStatus, CostImpact, ChecklistItem
} from "@/lib/types";

interface AnalysisSummaryProps {
  analysis: AnalysisResult;
  /** Document ID for export functionality */
  documentId: string;
  /** Callback when user clicks "View in spec" button */
  onViewInSpec?: (location: SpecLocation, quote: string | null) => void;
}

const severityColors: Record<string, string> = {
  low: "badge-low",
  medium: "badge-medium",
  high: "badge-high",
  critical: "badge-critical",
};

const severityLabels: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};

const responsibilityLabels: Record<Responsibility, string> = {
  gc: "General Contractor",
  mechanical: "Mechanical",
  electrical: "Electrical",
  plumbing: "Plumbing",
  controls: "Controls",
  owner: "Owner",
  shared: "Shared",
  unknown: "Unknown",
};

const responsibilityColors: Record<Responsibility, string> = {
  gc: "bg-gray-100 text-gray-700",
  mechanical: "bg-blue-100 text-blue-700",
  electrical: "bg-yellow-100 text-yellow-700",
  plumbing: "bg-cyan-100 text-cyan-700",
  controls: "bg-purple-100 text-purple-700",
  owner: "bg-green-100 text-green-700",
  shared: "bg-orange-100 text-orange-700",
  unknown: "bg-gray-100 text-gray-500",
};

const statusLabels: Record<RiskStatus, string> = {
  open: "Open",
  acknowledged: "Acknowledged",
  included_in_bid: "Included in Bid",
  will_clarify: "Will Clarify",
  accepted: "Accepted",
};

const goNoGoColors: Record<string, { bg: string; text: string; border: string }> = {
  proceed: { bg: "bg-green-50", text: "text-green-800", border: "border-green-300" },
  proceed_with_contingency: { bg: "bg-yellow-50", text: "text-yellow-800", border: "border-yellow-300" },
  caution: { bg: "bg-orange-50", text: "text-orange-800", border: "border-orange-300" },
  do_not_bid: { bg: "bg-red-50", text: "text-red-800", border: "border-red-300" },
};

const goNoGoLabels: Record<string, string> = {
  proceed: "PROCEED",
  proceed_with_contingency: "PROCEED WITH CONTINGENCY",
  caution: "CAUTION",
  do_not_bid: "DO NOT BID",
};

/** Format dollar amount with commas */
function formatDollars(amount: number | null | undefined): string {
  if (amount === null || amount === undefined) return "N/A";
  return "$" + amount.toLocaleString();
}

/** Helper to check if spec_location is a structured SpecLocation object */
function isSpecLocation(loc: SpecLocation | string | null | undefined): loc is SpecLocation {
  return loc !== null && loc !== undefined && typeof loc === "object" && "page" in loc;
}

/** Helper to format spec location for display */
function formatSpecLocation(loc: SpecLocation | string | null | undefined): string {
  if (!loc) return "Not found";
  if (typeof loc === "string") return loc;
  const parts: string[] = [];
  if (loc.section) parts.push(`Section ${loc.section}`);
  if (loc.page) parts.push(`Page ${loc.page}`);
  return parts.length > 0 ? parts.join(", ") : "Not found";
}

/** Format cost impact for display */
function formatCostImpact(costImpact: CostImpact | null | undefined): string {
  if (!costImpact) return "";
  if (costImpact.description) return costImpact.description;
  if (costImpact.min_dollars !== null && costImpact.max_dollars !== null) {
    return `${formatDollars(costImpact.min_dollars)} - ${formatDollars(costImpact.max_dollars)}`;
  }
  if (costImpact.percentage_of_contract !== null) {
    return `+${costImpact.percentage_of_contract}% of contract`;
  }
  return "";
}

/** Go/No-Go Recommendation Banner */
function GoNoGoBanner({ goNoGo, financialExposure }: { goNoGo: GoNoGo; financialExposure?: FinancialExposure | null }) {
  const colors = goNoGoColors[goNoGo.recommendation] || goNoGoColors.proceed;
  const label = goNoGoLabels[goNoGo.recommendation] || goNoGo.recommendation;

  return (
    <div className={`rounded-lg border-2 ${colors.bg} ${colors.border} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className={`text-xl font-bold ${colors.text}`}>{label}</span>
          {goNoGo.contingency_percent > 0 && (
            <span className={`text-sm font-medium px-2 py-1 rounded ${colors.bg} ${colors.text} border ${colors.border}`}>
              +{goNoGo.contingency_percent}% Contingency Recommended
            </span>
          )}
        </div>
        {financialExposure && (financialExposure.total_identified_min > 0 || financialExposure.total_identified_max > 0) && (
          <div className="text-right">
            <span className="text-xs text-gray-500">Estimated Risk Exposure</span>
            <p className={`text-lg font-bold ${colors.text}`}>
              {formatDollars(financialExposure.total_identified_min)} - {formatDollars(financialExposure.total_identified_max)}
            </p>
          </div>
        )}
      </div>

      {goNoGo.reasoning && (
        <p className={`text-sm ${colors.text} mb-3`}>{goNoGo.reasoning}</p>
      )}

      {goNoGo.key_concerns && goNoGo.key_concerns.length > 0 && (
        <div className="mt-2">
          <span className={`text-xs font-medium ${colors.text}`}>Key Concerns:</span>
          <ul className="mt-1 space-y-1">
            {goNoGo.key_concerns.map((concern, idx) => (
              <li key={idx} className={`text-sm ${colors.text} flex items-start`}>
                <span className="mr-2">•</span>
                {concern}
              </li>
            ))}
          </ul>
        </div>
      )}

      {financialExposure && (
        <div className="mt-3 pt-3 border-t border-opacity-30 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {financialExposure.ld_daily_rate && (
            <div>
              <span className="text-gray-500">LD Rate:</span>
              <p className={`font-medium ${colors.text}`}>{formatDollars(financialExposure.ld_daily_rate)}/day</p>
            </div>
          )}
          {financialExposure.ld_cap && (
            <div>
              <span className="text-gray-500">LD Cap:</span>
              <p className={`font-medium ${colors.text}`}>{formatDollars(financialExposure.ld_cap)}</p>
            </div>
          )}
          {financialExposure.bond_percentage && (
            <div>
              <span className="text-gray-500">Bond:</span>
              <p className={`font-medium ${colors.text}`}>{financialExposure.bond_percentage}%</p>
            </div>
          )}
          {financialExposure.retention_percentage && (
            <div>
              <span className="text-gray-500">Retention:</span>
              <p className={`font-medium ${colors.text}`}>{financialExposure.retention_percentage}%</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface RiskFlagCardProps {
  flag: RiskFlag;
  expanded: boolean;
  onToggle: () => void;
  onViewInSpec?: (location: SpecLocation, quote: string | null) => void;
}

function RiskFlagCard({ flag, expanded, onToggle, onViewInSpec }: RiskFlagCardProps) {
  // Check if we can show the "View in spec" button
  const hasViewableLocation = isSpecLocation(flag.spec_location) && flag.spec_location.page !== null;
  const costImpactStr = formatCostImpact(flag.cost_impact);
  const responsibility = flag.responsibility || "unknown";

  const handleViewInSpec = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent toggling the card
    if (hasViewableLocation && onViewInSpec) {
      onViewInSpec(flag.spec_location as SpecLocation, flag.source_quote || flag.source_text || null);
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg mb-3 overflow-hidden">
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            {flag.risk_id && (
              <span className="text-xs font-mono bg-gray-100 px-2 py-0.5 rounded">{flag.risk_id}</span>
            )}
            <h4 className="font-medium text-gray-900">{flag.title}</h4>
          </div>
          <div className="flex items-center space-x-2">
            {/* Cost Impact - new structured format */}
            {costImpactStr && (
              <span className="text-xs px-2 py-0.5 rounded font-medium text-red-600 bg-red-50 border border-red-200">
                {costImpactStr}
              </span>
            )}
            {/* Responsibility badge */}
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${responsibilityColors[responsibility]}`}>
              {responsibilityLabels[responsibility]}
            </span>
            <span className={`badge ${severityColors[flag.severity]}`}>
              {severityLabels[flag.severity]}
            </span>
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
        <p className="text-sm text-gray-600">{flag.description}</p>
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center space-x-2">
            {flag.category && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                {flag.category}
              </span>
            )}
          </div>
          {hasViewableLocation && onViewInSpec && (
            <button
              onClick={handleViewInSpec}
              className="inline-flex items-center px-2 py-1 text-xs text-white bg-primary-600 hover:bg-primary-700 rounded font-medium transition-colors"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Highlight in PDF
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-100 bg-gray-50">
          {/* Spec location info with highlight button */}
          <div className="mt-3 flex items-start justify-between">
            <div>
              <span className="text-xs font-medium text-gray-500">Spec Location:</span>
              <p className="text-sm text-gray-700">{formatSpecLocation(flag.spec_location)}</p>
            </div>
            {hasViewableLocation && onViewInSpec && (
              <button
                onClick={handleViewInSpec}
                className="inline-flex items-center px-3 py-1.5 text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg font-medium transition-colors shadow-sm"
              >
                <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                View Page {(flag.spec_location as SpecLocation).page}
              </button>
            )}
          </div>

          {/* Source quote (preferred) or source text (legacy) */}
          {(flag.source_quote || flag.source_text) && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">From Spec:</span>
              <p className="text-sm text-gray-600 italic bg-white rounded p-2 mt-1 border border-gray-200">
                &ldquo;{flag.source_quote || flag.source_text}&rdquo;
              </p>
            </div>
          )}

          {flag.impact && flag.impact.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">Impact:</span>
              <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                {flag.impact.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {flag.recommended_action && flag.recommended_action.length > 0 && (
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">Recommended Actions:</span>
              <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                {flag.recommended_action.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ProjectSummaryCard({ summary }: { summary: ProjectSummary }) {
  return (
    <div className="card mb-6 bg-blue-50 border border-blue-200">
      <h4 className="font-medium text-blue-900 mb-3">Project Summary</h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        {summary.project_name && (
          <div>
            <span className="text-blue-700 font-medium">Project:</span>
            <p className="text-blue-900">{summary.project_name}</p>
          </div>
        )}
        {summary.location && (
          <div>
            <span className="text-blue-700 font-medium">Location:</span>
            <p className="text-blue-900">{summary.location}</p>
          </div>
        )}
        {summary.project_type && (
          <div>
            <span className="text-blue-700 font-medium">Type:</span>
            <p className="text-blue-900">{summary.project_type}</p>
          </div>
        )}
        {summary.schedule_constraints && (
          <div>
            <span className="text-blue-700 font-medium">Schedule:</span>
            <p className="text-blue-900">{summary.schedule_constraints}</p>
          </div>
        )}
      </div>
      {summary.scope_description && (
        <div className="mt-3">
          <span className="text-blue-700 font-medium text-sm">Scope:</span>
          <p className="text-blue-900 text-sm">{summary.scope_description}</p>
        </div>
      )}
    </div>
  );
}

/** Helper to get checklist item text - handles both string and structured format */
function getChecklistItemText(item: ChecklistItem | string): string {
  if (typeof item === "string") return item;
  return item.item;
}

/** Helper to get checklist item extra info */
function getChecklistItemExtra(item: ChecklistItem | string): { category?: string; cost?: string; priority?: string } {
  if (typeof item === "string") return {};
  return {
    category: item.category || undefined,
    cost: item.estimated_cost || undefined,
    priority: item.priority || undefined,
  };
}

function ChecklistSection({ checklist }: { checklist: EstimatorChecklist }) {
  return (
    <section className="mt-8">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Estimator Checklist</h3>
      <div className="grid md:grid-cols-3 gap-4">
        {checklist.must_confirm_before_pricing && checklist.must_confirm_before_pricing.length > 0 && (
          <div className="card bg-yellow-50 border border-yellow-200">
            <h4 className="font-medium text-yellow-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Confirm Before Pricing
            </h4>
            <ul className="space-y-2 text-sm text-yellow-900">
              {checklist.must_confirm_before_pricing.map((item, idx) => {
                const extra = getChecklistItemExtra(item);
                return (
                  <li key={idx} className="flex items-start">
                    <input type="checkbox" className="mt-1 mr-2" />
                    <div>
                      <span>{getChecklistItemText(item)}</span>
                      {extra.category && (
                        <span className="ml-2 text-xs bg-yellow-200 px-1.5 py-0.5 rounded">{extra.category}</span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {checklist.include_in_bid_cost && checklist.include_in_bid_cost.length > 0 && (
          <div className="card bg-green-50 border border-green-200">
            <h4 className="font-medium text-green-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Include in Bid Cost
            </h4>
            <ul className="space-y-2 text-sm text-green-900">
              {checklist.include_in_bid_cost.map((item, idx) => {
                const extra = getChecklistItemExtra(item);
                return (
                  <li key={idx} className="flex items-start">
                    <input type="checkbox" className="mt-1 mr-2" />
                    <div>
                      <span>{getChecklistItemText(item)}</span>
                      {extra.cost && (
                        <span className="ml-2 text-xs font-medium text-green-700">{extra.cost}</span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {checklist.clarify_via_rfi && checklist.clarify_via_rfi.length > 0 && (
          <div className="card bg-purple-50 border border-purple-200">
            <h4 className="font-medium text-purple-800 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Clarify via RFI
            </h4>
            <ul className="space-y-2 text-sm text-purple-900">
              {checklist.clarify_via_rfi.map((item, idx) => {
                const extra = getChecklistItemExtra(item);
                return (
                  <li key={idx} className="flex items-start">
                    <input type="checkbox" className="mt-1 mr-2" />
                    <div>
                      <span>{getChecklistItemText(item)}</span>
                      {extra.priority === "high" && (
                        <span className="ml-2 text-xs bg-red-200 text-red-700 px-1.5 py-0.5 rounded">HIGH</span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}

function ExtractionField({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;

  return (
    <div className="mb-4">
      <h4 className="text-sm font-medium text-gray-700 mb-1">{label}</h4>
      <p className="text-sm text-gray-600 bg-gray-50 rounded p-3">{value}</p>
    </div>
  );
}

export default function AnalysisSummary({ analysis, documentId, onViewInSpec }: AnalysisSummaryProps) {
  const { extraction, risk_report } = analysis;
  const [expandedFlags, setExpandedFlags] = useState<Set<number>>(new Set());
  const [exporting, setExporting] = useState<"pdf" | "excel" | null>(null);

  const toggleFlag = (idx: number) => {
    const newExpanded = new Set(expandedFlags);
    if (newExpanded.has(idx)) {
      newExpanded.delete(idx);
    } else {
      newExpanded.add(idx);
    }
    setExpandedFlags(newExpanded);
  };

  const expandAll = () => {
    setExpandedFlags(new Set(risk_report.flags.map((_, idx) => idx)));
  };

  const collapseAll = () => {
    setExpandedFlags(new Set());
  };

  const handleExportPdf = async () => {
    setExporting("pdf");
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const response = await fetch(`${apiBase}/api/v1/documents/${documentId}/export-pdf`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Export failed");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = response.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "") || "risk_report.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error("PDF export failed:", error);
      alert("Failed to export PDF. Please try again.");
    } finally {
      setExporting(null);
    }
  };

  const handleExportExcel = async () => {
    setExporting("excel");
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
      const response = await fetch(`${apiBase}/api/v1/documents/${documentId}/export-excel`, {
        credentials: "include",
      });
      if (!response.ok) throw new Error("Export failed");
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = response.headers.get("Content-Disposition")?.split("filename=")[1]?.replace(/"/g, "") || "risk_log.xlsx";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      console.error("Excel export failed:", error);
      alert("Failed to export Excel. Please try again.");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Export CYA Package Buttons */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <h2 className="text-xl font-bold text-gray-900">Bid Risk Intelligence Report</h2>
        <div className="flex items-center space-x-3">
          <span className="text-sm text-gray-500 mr-2">Export CYA Package:</span>
          <button
            onClick={handleExportPdf}
            disabled={exporting !== null}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:bg-gray-400 rounded-lg shadow-sm transition-colors"
          >
            {exporting === "pdf" ? (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            )}
            PDF Report
          </button>
          <button
            onClick={handleExportExcel}
            disabled={exporting !== null}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-lg shadow-sm transition-colors"
          >
            {exporting === "excel" ? (
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
            Excel Log
          </button>
        </div>
      </div>

      {/* Go/No-Go Recommendation Banner - Top Priority */}
      {risk_report.go_no_go && (
        <GoNoGoBanner
          goNoGo={risk_report.go_no_go as GoNoGo}
          financialExposure={risk_report.financial_exposure as FinancialExposure | undefined}
        />
      )}

      {/* Project Summary */}
      {risk_report.project_summary && (
        <ProjectSummaryCard summary={risk_report.project_summary as ProjectSummary} />
      )}

      {/* Risk Overview */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Risk Assessment</h3>
          <span className={`badge ${severityColors[risk_report.overall_risk_level]}`}>
            Overall: {severityLabels[risk_report.overall_risk_level]}
          </span>
        </div>

        <div className="card mb-4">
          <p className="text-gray-700">{risk_report.overall_summary}</p>
          <div className="mt-3 flex space-x-4 text-sm">
            <span className="text-gray-500">
              Total Flags: <strong>{risk_report.total_flags}</strong>
            </span>
            <span className="text-red-600">
              High Severity: <strong>{risk_report.high_severity_count}</strong>
            </span>
          </div>
        </div>

        {risk_report.flags.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-700">Risk Flags</h4>
              <div className="space-x-2">
                <button
                  onClick={expandAll}
                  className="text-xs text-primary-600 hover:text-primary-800"
                >
                  Expand All
                </button>
                <span className="text-gray-300">|</span>
                <button
                  onClick={collapseAll}
                  className="text-xs text-primary-600 hover:text-primary-800"
                >
                  Collapse All
                </button>
              </div>
            </div>
            {risk_report.flags.map((flag, idx) => (
              <RiskFlagCard
                key={idx}
                flag={flag}
                expanded={expandedFlags.has(idx)}
                onToggle={() => toggleFlag(idx)}
                onViewInSpec={onViewInSpec}
              />
            ))}
          </div>
        )}
      </section>

      {/* Estimator Checklist */}
      {risk_report.estimator_checklist && (
        <ChecklistSection checklist={risk_report.estimator_checklist as EstimatorChecklist} />
      )}

      {/* Key Requirements */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Requirements</h3>
        <div className="card">
          <ExtractionField label="Insurance Requirements" value={extraction.insurance_requirements} />
          <ExtractionField label="Bonding Requirements" value={extraction.bonding_requirements} />
          <ExtractionField label="Warranty Requirements" value={extraction.warranty_requirements} />
          <ExtractionField label="Liquidated Damages" value={extraction.liquidated_damages} />
          <ExtractionField label="Testing Requirements" value={extraction.testing_requirements} />
          <ExtractionField label="Commissioning Requirements" value={extraction.commissioning_requirements} />
          <ExtractionField label="Submittals Summary" value={extraction.submittals_summary} />
        </div>
      </section>

      {/* Division Summaries */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Division Requirements</h3>
        <div className="card">
          <ExtractionField label="Division 22 - Plumbing" value={extraction.div22_requirements} />
          <ExtractionField label="Division 23 - HVAC" value={extraction.div23_requirements} />
          <ExtractionField label="Division 26 - Electrical" value={extraction.div26_requirements} />
        </div>
      </section>
    </div>
  );
}
