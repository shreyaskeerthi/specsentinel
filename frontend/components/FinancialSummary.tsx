"use client";

import React from "react";
// analysis prop is the full API response

function formatDollars(n: number | null | undefined): string {
  if (n == null || n === 0) return "$0";
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `$${Math.round(n / 1_000)}K`;
  return `$${n.toLocaleString()}`;
}

export default function FinancialSummary({ analysis, contractValue, budget }: { analysis: any; contractValue?: number; budget?: number }) {
  const fin = analysis.risk_report?.financial_exposure;
  const flags: any[] = analysis.risk_report?.flags || [];
  const gng = analysis.risk_report?.go_no_go;

  // Aggregate cost drivers from flags
  const costDrivers = flags
    .filter((f: any) => f.cost_impact && f.cost_impact.type !== "none")
    .sort((a: any, b: any) => {
      const aMax = a.cost_impact?.max_dollars || 0;
      const bMax = b.cost_impact?.max_dollars || 0;
      return bMax - aMax;
    })
    .slice(0, 8);

  return (
    <div className="space-y-4">
      {/* Contract & Budget Context */}
      {(contractValue || budget) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {contractValue && (
            <div className="card text-center">
              <p className="text-xs text-gray-500 uppercase">Contract Value</p>
              <p className="text-2xl font-bold text-green-400">{formatDollars(contractValue)}</p>
            </div>
          )}
          {budget && (
            <div className="card text-center">
              <p className="text-xs text-gray-500 uppercase">Internal Budget</p>
              <p className="text-2xl font-bold text-blue-400">{formatDollars(budget)}</p>
            </div>
          )}
          {contractValue && budget && (
            <div className="card text-center">
              <p className="text-xs text-gray-500 uppercase">Margin</p>
              <p className={`text-2xl font-bold ${contractValue - budget > 0 ? "text-green-400" : "text-red-400"}`}>
                {formatDollars(contractValue - budget)}
              </p>
            </div>
          )}
          {fin && contractValue && (
            <div className="card text-center">
              <p className="text-xs text-gray-500 uppercase">Exposure vs Contract</p>
              <p className="text-2xl font-bold text-red-400">
                {((fin.total_identified_max / contractValue) * 100).toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* Total Exposure Hero */}
      <div className="card border-red-900/50">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Financial Exposure</p>
            <p className="text-3xl font-black text-white mt-1">
              {fin ? `${formatDollars(fin.total_identified_min)} — ${formatDollars(fin.total_identified_max)}` : "Not calculated"}
            </p>
          </div>
          {gng && gng.contingency_percent > 0 && (
            <div className="text-right">
              <p className="text-xs text-gray-500 uppercase">Suggested Contingency</p>
              <p className="text-3xl font-black text-yellow-400">{gng.contingency_percent}%</p>
              {contractValue && (
                <p className="text-sm text-gray-400">{formatDollars(contractValue * gng.contingency_percent / 100)}</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Key Financial Metrics */}
      {fin && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="card">
            <p className="text-xs text-gray-500">LD Daily Rate</p>
            <p className="text-lg font-bold text-white">{fin.ld_daily_rate ? formatDollars(fin.ld_daily_rate) + "/day" : "Not specified"}</p>
          </div>
          <div className="card">
            <p className="text-xs text-gray-500">LD Cap</p>
            <p className="text-lg font-bold text-white">{fin.ld_cap ? formatDollars(fin.ld_cap) : "Not specified"}</p>
          </div>
          <div className="card">
            <p className="text-xs text-gray-500">Bond Requirement</p>
            <p className="text-lg font-bold text-white">{fin.bond_percentage ? `${fin.bond_percentage}%` : "Not specified"}</p>
          </div>
          <div className="card">
            <p className="text-xs text-gray-500">Retention</p>
            <p className="text-lg font-bold text-white">{fin.retention_percentage ? `${fin.retention_percentage}%` : "Not specified"}</p>
          </div>
        </div>
      )}

      {/* Top Cost Drivers */}
      {costDrivers.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">Top Cost Drivers</h3>
          <div className="space-y-3">
            {costDrivers.map((flag, i) => {
              const ci = flag.cost_impact!;
              const maxVal = costDrivers[0].cost_impact?.max_dollars || 1;
              const barWidth = ci.max_dollars ? Math.min((ci.max_dollars / maxVal) * 100, 100) : 20;

              return (
                <div key={i}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`badge-${flag.severity}`}>{flag.severity}</span>
                      <span className="text-sm text-gray-200">{flag.title}</span>
                    </div>
                    <span className="text-sm font-mono text-gray-300">
                      {ci.description || (ci.min_dollars && ci.max_dollars
                        ? `${formatDollars(ci.min_dollars)} - ${formatDollars(ci.max_dollars)}`
                        : ci.percentage_of_contract
                        ? `+${ci.percentage_of_contract}%`
                        : "TBD")}
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        flag.severity === "critical" ? "bg-red-500" :
                        flag.severity === "high" ? "bg-orange-500" :
                        flag.severity === "medium" ? "bg-yellow-500" : "bg-green-500"
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Exposure Breakdown by Category */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-400 uppercase mb-3">Exposure by Category</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {["warranty", "penalty", "bonding", "insurance", "testing", "commissioning", "schedule", "scope"].map((cat) => {
            const catFlags = flags.filter((f) => f.type === cat && f.cost_impact && f.cost_impact.type !== "none");
            if (catFlags.length === 0) return null;
            const minTotal = catFlags.reduce((sum, f) => sum + (f.cost_impact?.min_dollars || 0), 0);
            const maxTotal = catFlags.reduce((sum, f) => sum + (f.cost_impact?.max_dollars || 0), 0);
            return (
              <div key={cat} className="flex items-center justify-between bg-gray-800/50 rounded-lg px-3 py-2">
                <span className="text-sm text-gray-300 capitalize">{cat}</span>
                <span className="text-sm font-mono text-gray-400">
                  {formatDollars(minTotal)} - {formatDollars(maxTotal)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
