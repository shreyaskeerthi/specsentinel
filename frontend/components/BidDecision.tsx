"use client";

import React from "react";
import type { GoNoGoRecommendation } from "@/lib/types";

const RECOMMENDATION_CONFIG: Record<GoNoGoRecommendation, { label: string; color: string; bg: string; border: string }> = {
  proceed: { label: "PROCEED", color: "text-green-400", bg: "bg-green-950/40", border: "border-green-700" },
  proceed_with_contingency: { label: "PROCEED W/ CONTINGENCY", color: "text-yellow-400", bg: "bg-yellow-950/40", border: "border-yellow-700" },
  caution: { label: "CAUTION", color: "text-orange-400", bg: "bg-orange-950/40", border: "border-orange-700" },
  do_not_bid: { label: "DO NOT BID", color: "text-red-400", bg: "bg-red-950/40", border: "border-red-700" },
};

function formatDollars(n: number | null | undefined): string {
  if (n == null || n === 0) return "$0";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`;
  return `$${n.toLocaleString()}`;
}

export default function BidDecision({ analysis, contractValue }: { analysis: any; contractValue?: number }) {
  const rr = analysis.risk_report;
  const gng = rr.go_no_go;
  const fin = rr.financial_exposure;
  const ps = rr.project_summary;

  const rec = (gng?.recommendation || "proceed") as GoNoGoRecommendation;
  const config = RECOMMENDATION_CONFIG[rec] || RECOMMENDATION_CONFIG.proceed;

  return (
    <div className="space-y-4">
      {/* Hero Decision Card */}
      <div className={`rounded-xl border-2 ${config.border} ${config.bg} p-6`}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Bid Recommendation</p>
            <h2 className={`text-3xl font-black ${config.color}`}>{config.label}</h2>
            {gng?.reasoning && (
              <p className="text-gray-300 mt-2 max-w-2xl">{gng.reasoning}</p>
            )}
          </div>
          <div className="text-right">
            {gng && gng.contingency_percent > 0 && (
              <div>
                <p className="text-xs text-gray-500 uppercase">Contingency</p>
                <p className="text-2xl font-bold text-white">{gng.contingency_percent}%</p>
              </div>
            )}
          </div>
        </div>

        {/* Key Concerns */}
        {gng?.key_concerns && gng.key_concerns.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-700/50">
            <p className="text-xs font-semibold text-gray-400 uppercase mb-2">Top Concerns</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {gng.key_concerns.map((c: string, i: number) => (
                <div key={i} className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5 font-bold">{i + 1}.</span>
                  <span className="text-sm text-gray-300">{c}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        {contractValue && (
          <div className="card text-center">
            <p className="text-xs text-gray-500 uppercase">Contract Value</p>
            <p className="text-xl font-bold text-green-400">{formatDollars(contractValue)}</p>
          </div>
        )}
        <div className="card text-center">
          <p className="text-xs text-gray-500 uppercase">Risk Level</p>
          <p className={`text-lg font-bold badge-${rr.overall_risk_level} mt-1 inline-block`}>
            {rr.overall_risk_level.toUpperCase()}
          </p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 uppercase">Total Flags</p>
          <p className="text-2xl font-bold text-white">{rr.total_flags}</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 uppercase">High/Critical</p>
          <p className="text-2xl font-bold text-red-400">{rr.high_severity_count}</p>
        </div>
        <div className="card text-center">
          <p className="text-xs text-gray-500 uppercase">Exposure Range</p>
          <p className="text-lg font-bold text-white">
            {fin ? `${formatDollars(fin.total_identified_min)} - ${formatDollars(fin.total_identified_max)}` : "N/A"}
          </p>
        </div>
      </div>

      {/* Project Summary */}
      {ps && typeof ps === "object" && "project_name" in ps && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">Project Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            {ps.project_name && (
              <div>
                <p className="text-gray-500">Project</p>
                <p className="text-gray-200 font-medium">{ps.project_name}</p>
              </div>
            )}
            {ps.location && (
              <div>
                <p className="text-gray-500">Location</p>
                <p className="text-gray-200 font-medium">{ps.location}</p>
              </div>
            )}
            {ps.project_type && (
              <div>
                <p className="text-gray-500">Type</p>
                <p className="text-gray-200 font-medium capitalize">{ps.project_type}</p>
              </div>
            )}
            {ps.schedule_constraints && (
              <div>
                <p className="text-gray-500">Schedule</p>
                <p className="text-gray-200 font-medium">{ps.schedule_constraints}</p>
              </div>
            )}
            {ps.scope_description && (
              <div className="col-span-2 md:col-span-4">
                <p className="text-gray-500">Scope</p>
                <p className="text-gray-200">{ps.scope_description}</p>
              </div>
            )}
          </div>
          <div className="flex gap-4 mt-3">
            {ps.occupied_building != null && (
              <span className={`text-xs px-2 py-1 rounded ${ps.occupied_building ? "bg-orange-900/30 text-orange-400" : "bg-gray-800 text-gray-400"}`}>
                {ps.occupied_building ? "Occupied Building" : "Unoccupied"}
              </span>
            )}
            {ps.union_required != null && (
              <span className={`text-xs px-2 py-1 rounded ${ps.union_required ? "bg-blue-900/30 text-blue-400" : "bg-gray-800 text-gray-400"}`}>
                {ps.union_required ? "Union Required" : "Non-Union"}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Overall Summary */}
      <div className="card">
        <p className="text-gray-300">{rr.overall_summary}</p>
      </div>
    </div>
  );
}
