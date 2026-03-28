"use client";

import React, { useState } from "react";
import type { RiskFlag } from "@/lib/types";

function formatDollars(n: number | null | undefined): string {
  if (n == null || n === 0) return "$0";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${Math.round(n / 1_000)}K`;
  return `$${n.toLocaleString()}`;
}

export default function RiskFlags({ flags }: { flags: RiskFlag[] }) {
  const [filter, setFilter] = useState<string>("all");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
  const sorted = [...flags].sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  const filtered = filter === "all" ? sorted : sorted.filter((f) => f.severity === filter);

  const toggle = (i: number) => {
    const next = new Set(expanded);
    next.has(i) ? next.delete(i) : next.add(i);
    setExpanded(next);
  };

  const counts = {
    all: flags.length,
    critical: flags.filter((f) => f.severity === "critical").length,
    high: flags.filter((f) => f.severity === "high").length,
    medium: flags.filter((f) => f.severity === "medium").length,
    low: flags.filter((f) => f.severity === "low").length,
  };

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex gap-2 flex-wrap">
        {(["all", "critical", "high", "medium", "low"] as const).map((sev) => (
          <button
            key={sev}
            onClick={() => setFilter(sev)}
            className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors ${
              filter === sev
                ? sev === "all" ? "bg-blue-600 text-white"
                  : sev === "critical" ? "bg-red-600 text-white"
                  : sev === "high" ? "bg-orange-600 text-white"
                  : sev === "medium" ? "bg-yellow-600 text-white"
                  : "bg-green-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {sev === "all" ? "All" : sev.charAt(0).toUpperCase() + sev.slice(1)} ({counts[sev]})
          </button>
        ))}
      </div>

      {/* Risk list */}
      <div className="space-y-2">
        {filtered.map((flag, i) => {
          const isExpanded = expanded.has(i);
          const ci = flag.cost_impact;
          const loc = flag.spec_location;
          const page = typeof loc === "object" && loc?.page ? loc.page : null;

          return (
            <div
              key={i}
              className="card cursor-pointer hover:border-gray-700 transition-colors"
              onClick={() => toggle(i)}
            >
              {/* Header row */}
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <span className={`badge-${flag.severity} mt-0.5 shrink-0`}>{flag.severity}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm font-semibold text-gray-100">{flag.title}</h4>
                      {flag.category && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">{flag.category}</span>
                      )}
                      {flag.responsibility && flag.responsibility !== "unknown" && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400 capitalize">{flag.responsibility}</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{flag.description}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 ml-3">
                  {ci && ci.type !== "none" && (
                    <span className="text-xs font-mono text-gray-300">
                      {ci.min_dollars && ci.max_dollars
                        ? `${formatDollars(ci.min_dollars)}-${formatDollars(ci.max_dollars)}`
                        : ci.description || ""}
                    </span>
                  )}
                  {page && (
                    <span className="text-[10px] text-gray-600">p.{page}</span>
                  )}
                  <svg className={`w-4 h-4 text-gray-600 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-gray-800 space-y-3">
                  <p className="text-sm text-gray-300">{flag.description}</p>

                  {flag.source_quote && (
                    <div className="bg-gray-800/50 rounded-lg px-3 py-2">
                      <p className="text-xs text-gray-500 mb-1">Source Quote</p>
                      <p className="text-sm text-gray-300 italic">&ldquo;{flag.source_quote}&rdquo;</p>
                    </div>
                  )}

                  {flag.impact && flag.impact.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Why it matters</p>
                      <ul className="space-y-1">
                        {flag.impact.map((item, j) => (
                          <li key={j} className="text-sm text-gray-400 flex items-start gap-1.5">
                            <span className="text-red-500 mt-1">-</span> {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {flag.recommended_action && flag.recommended_action.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Recommended Actions</p>
                      <ul className="space-y-1">
                        {flag.recommended_action.map((item, j) => (
                          <li key={j} className="text-sm text-blue-400 flex items-start gap-1.5">
                            <span className="text-blue-600 mt-1">-</span> {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
