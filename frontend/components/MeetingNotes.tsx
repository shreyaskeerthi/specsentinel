"use client";

import React, { useState, useEffect } from "react";
import type { MeetingAnalysis, MeetingNoteSummary } from "@/lib/types";
import { listMeetingNotes } from "@/lib/api";

interface MeetingNotesProps {
  onAnalyze: (notes: string, title?: string) => Promise<void>;
  meetingResult: MeetingAnalysis | null;
  disabled: boolean;
  projectId: string;
}

export default function MeetingNotes({ onAnalyze, meetingResult, disabled, projectId }: MeetingNotesProps) {
  const [notes, setNotes] = useState("");
  const [title, setTitle] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [history, setHistory] = useState<MeetingNoteSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    setHistoryLoading(true);
    listMeetingNotes(projectId)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }, [projectId, meetingResult]);

  const handleSubmit = async () => {
    if (!notes.trim()) return;
    setAnalyzing(true);
    try {
      await onAnalyze(notes, title.trim() || undefined);
      setShowResult(true);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
          <span className="text-gray-300 font-medium">Meeting Notes</span>
        </div>
        {history.length > 0 && (
          <button onClick={() => setShowHistory(!showHistory)} className="btn-ghost text-xs">
            {showHistory ? "Hide" : "History"} ({history.length})
          </button>
        )}
      </div>

      {/* History list */}
      {showHistory && (
        <div className="mb-3 space-y-1 border-b border-gray-800 pb-3">
          {historyLoading ? (
            <p className="text-xs text-gray-500">Loading...</p>
          ) : (
            history.map((m) => (
              <div key={m.id} className="flex items-start gap-2 py-1">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-300 truncate">{m.title}</p>
                  {m.summary && <p className="text-xs text-gray-500 truncate">{m.summary}</p>}
                </div>
                <div className="text-right shrink-0">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${m.status === "completed" ? "bg-green-900/40 text-green-400" : "bg-gray-700 text-gray-400"}`}>
                    {m.status}
                  </span>
                  {m.attendee_count > 0 && (
                    <p className="text-[10px] text-gray-600 mt-0.5">{m.attendee_count} attendees</p>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Title input */}
      <input
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500 mb-2"
        placeholder="Meeting title (optional)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        disabled={disabled}
      />

      <textarea
        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
        rows={3}
        placeholder={disabled ? "Upload a spec first..." : "Paste meeting transcript or minutes to extract decisions, risks, and tasks..."}
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
          {/* Summary */}
          {meetingResult.summary && (
            <div className="bg-gray-800/60 rounded-lg px-3 py-2 text-sm text-gray-300">
              {meetingResult.summary}
            </div>
          )}

          {/* Attendees */}
          {meetingResult.attendees && meetingResult.attendees.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">Attendees</h4>
              <div className="flex flex-wrap gap-1">
                {meetingResult.attendees.map((a, i) => (
                  <span key={i} className="text-xs bg-gray-700 rounded px-2 py-0.5 text-gray-300">
                    {a.name}{a.role ? ` · ${a.role}` : ""}
                  </span>
                ))}
              </div>
            </div>
          )}

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
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">Risks</h4>
              {meetingResult.new_risks.map((r, i) => (
                <div key={i} className="text-sm mb-1">
                  <span className={`badge-${r.severity} mr-1`}>{r.severity}</span>
                  <span className="text-gray-300">{r.title}</span>
                  {!r.is_new && r.related_risk_id && (
                    <span className="text-xs text-green-400 ml-1">(updated {r.related_risk_id})</span>
                  )}
                  {r.cost_impact_description && <span className="text-red-400 text-xs ml-1">{r.cost_impact_description}</span>}
                </div>
              ))}
            </div>
          )}

          {meetingResult.schedule_events && meetingResult.schedule_events.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">Schedule Events ({meetingResult.schedule_events.length} added to timeline)</h4>
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
