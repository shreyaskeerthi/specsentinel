"use client";

import React, { useState } from "react";
import type { MeetingAnalysis } from "@/lib/types";

interface MeetingNotesProps {
  onAnalyze: (notes: string) => Promise<void>;
  meetingResult: MeetingAnalysis | null;
  disabled: boolean;
}

export default function MeetingNotes({ onAnalyze, meetingResult, disabled }: MeetingNotesProps) {
  const [notes, setNotes] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [showResult, setShowResult] = useState(false);

  const handleSubmit = async () => {
    if (!notes.trim()) return;
    setAnalyzing(true);
    try {
      await onAnalyze(notes);
      setShowResult(true);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-2">
        <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
        <span className="text-gray-300 font-medium">Meeting Notes</span>
      </div>

      <textarea
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        rows={2}
        placeholder={disabled ? "Upload a spec first..." : "Paste meeting minutes to extract decisions, risks, and tasks..."}
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        disabled={disabled}
      />

      <div className="flex items-center justify-between mt-2">
        <button
          onClick={handleSubmit}
          disabled={disabled || analyzing || !notes.trim()}
          className="btn-secondary text-sm"
        >
          {analyzing ? "Analyzing..." : "Analyze Notes"}
        </button>

        {meetingResult && (
          <button
            onClick={() => setShowResult(!showResult)}
            className="btn-ghost text-xs"
          >
            {showResult ? "Hide" : "Show"} Results ({meetingResult.key_decisions.length} decisions, {meetingResult.new_risks.length} risks)
          </button>
        )}
      </div>

      {/* Inline meeting results */}
      {showResult && meetingResult && (
        <div className="mt-3 space-y-3 border-t border-gray-800 pt-3">
          {meetingResult.financial_impact_summary && (
            <div className="bg-yellow-900/20 border border-yellow-800/50 rounded-lg px-3 py-2 text-sm text-yellow-400">
              {meetingResult.financial_impact_summary}
            </div>
          )}

          {meetingResult.key_decisions.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">Decisions</h4>
              {meetingResult.key_decisions.map((d, i) => (
                <div key={i} className="text-sm text-gray-300 mb-1">
                  <span className="text-blue-400 mr-1">-</span> {d.decision}
                  {d.impact && <span className="text-gray-500 text-xs ml-1">({d.impact})</span>}
                </div>
              ))}
            </div>
          )}

          {meetingResult.new_risks.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">New Risks (merged into analysis)</h4>
              {meetingResult.new_risks.map((r, i) => (
                <div key={i} className="text-sm mb-1">
                  <span className={`badge-${r.severity} mr-1`}>{r.severity}</span>
                  <span className="text-gray-300">{r.title}</span>
                  {r.cost_impact_description && <span className="text-red-400 text-xs ml-1">{r.cost_impact_description}</span>}
                </div>
              ))}
            </div>
          )}

          {meetingResult.schedule_events && meetingResult.schedule_events.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">Schedule Events ({meetingResult.schedule_events.length})</h4>
              {meetingResult.schedule_events.map((s, i) => (
                <div key={i} className="text-sm mb-1 flex items-center gap-2">
                  <span className="text-blue-400 font-mono text-xs">{s.date}</span>
                  <span className="text-gray-300">{s.title}</span>
                  <span className="text-[10px] text-gray-600">{s.type}</span>
                </div>
              ))}
            </div>
          )}

          {meetingResult.revised_exposure_max && (
            <div className="bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2 text-sm text-red-400">
              Revised exposure: ${meetingResult.revised_exposure_min?.toLocaleString()} — ${meetingResult.revised_exposure_max?.toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
