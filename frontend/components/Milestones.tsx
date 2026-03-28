"use client";

import React, { useState } from "react";

interface MilestoneItem {
  id: string;
  title: string;
  date: string;
  phase: string;
  type: string;
  description: string | null;
  status: string;
  assignee: string | null;
}

interface MilestonesByPhase {
  preconstruction: MilestoneItem[];
  construction: MilestoneItem[];
  closeout: MilestoneItem[];
}

const PHASES = [
  { key: "preconstruction", label: "Preconstruction", color: "text-blue-400", border: "border-blue-800", bg: "bg-blue-900/20" },
  { key: "construction", label: "Construction", color: "text-green-400", border: "border-green-800", bg: "bg-green-900/20" },
  { key: "closeout", label: "Closeout", color: "text-purple-400", border: "border-purple-800", bg: "bg-purple-900/20" },
] as const;

const TYPE_OPTIONS = ["milestone", "deadline", "task", "blackout", "meeting"];
const STATUS_COLORS: Record<string, string> = {
  pending: "bg-gray-800 text-gray-400",
  in_progress: "bg-blue-900/40 text-blue-400",
  completed: "bg-green-900/40 text-green-400",
  missed: "bg-red-900/40 text-red-400",
};

function daysUntil(d: string): number {
  const target = new Date(d + "T00:00:00");
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / 86400000);
}

interface MilestonesProps {
  milestones: MilestonesByPhase;
  onAdd: (data: { title: string; date: string; phase: string; type: string; description?: string; assignee?: string }) => Promise<void>;
  onUpdate: (id: string, data: any) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}

export default function Milestones({ milestones, onAdd, onUpdate, onDelete }: MilestonesProps) {
  const [addingPhase, setAddingPhase] = useState<string | null>(null);
  const [form, setForm] = useState({ title: "", date: "", type: "milestone", description: "", assignee: "" });
  const [saving, setSaving] = useState(false);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addingPhase) return;
    setSaving(true);
    try {
      await onAdd({
        title: form.title,
        date: form.date,
        phase: addingPhase,
        type: form.type,
        description: form.description || undefined,
        assignee: form.assignee || undefined,
      });
      setForm({ title: "", date: "", type: "milestone", description: "", assignee: "" });
      setAddingPhase(null);
    } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (item: MilestoneItem) => {
    const next = item.status === "completed" ? "pending" : item.status === "pending" ? "in_progress" : "completed";
    await onUpdate(item.id, { status: next });
  };

  return (
    <div className="space-y-6">
      {PHASES.map((phase) => {
        const items = milestones[phase.key as keyof MilestonesByPhase] || [];
        return (
          <div key={phase.key}>
            {/* Phase header */}
            <div className={`flex items-center justify-between mb-3 pb-2 border-b ${phase.border}`}>
              <div className="flex items-center gap-2">
                <h3 className={`text-sm font-semibold uppercase ${phase.color}`}>{phase.label}</h3>
                <span className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">{items.length}</span>
              </div>
              <button
                onClick={() => setAddingPhase(addingPhase === phase.key ? null : phase.key)}
                className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-800"
              >
                + Add
              </button>
            </div>

            {/* Add form */}
            {addingPhase === phase.key && (
              <div className={`card mb-3 ${phase.border} border`}>
                <form onSubmit={handleAdd} className="space-y-2">
                  <div className="grid grid-cols-3 gap-2">
                    <input required value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="Title *" />
                    <input type="date" required value={form.date} onChange={(e) => setForm((p) => ({ ...p, date: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500" />
                    <select value={form.type} onChange={(e) => setForm((p) => ({ ...p, type: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500">
                      {TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <input value={form.description} onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="Description (optional)" />
                    <input value={form.assignee} onChange={(e) => setForm((p) => ({ ...p, assignee: e.target.value }))}
                      className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      placeholder="Assignee (optional)" />
                  </div>
                  <div className="flex gap-2">
                    <button type="submit" disabled={saving} className="btn-primary text-xs">{saving ? "Adding..." : "Add"}</button>
                    <button type="button" onClick={() => setAddingPhase(null)} className="btn-secondary text-xs">Cancel</button>
                  </div>
                </form>
              </div>
            )}

            {/* Items */}
            {items.length === 0 && addingPhase !== phase.key ? (
              <div className={`rounded-lg border border-dashed ${phase.border} px-4 py-3 text-center`}>
                <p className="text-xs text-gray-600">No {phase.label.toLowerCase()} milestones yet</p>
              </div>
            ) : (
              <div className="space-y-1">
                {items.map((item) => {
                  const days = daysUntil(item.date);
                  const isPast = days < 0;
                  const isUrgent = days >= 0 && days <= 5;

                  return (
                    <div key={item.id} className={`flex items-center gap-3 rounded-lg border border-gray-800 px-3 py-2 ${phase.bg} ${isPast && item.status !== "completed" ? "opacity-60" : ""}`}>
                      {/* Status toggle */}
                      <button
                        onClick={() => toggleStatus(item)}
                        className={`w-5 h-5 rounded border shrink-0 flex items-center justify-center transition-colors ${
                          item.status === "completed"
                            ? "bg-green-600 border-green-600 text-white"
                            : item.status === "in_progress"
                            ? "bg-blue-600/30 border-blue-600"
                            : "border-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {item.status === "completed" && (
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                          </svg>
                        )}
                      </button>

                      {/* Date */}
                      <div className="w-20 shrink-0">
                        <p className={`text-xs font-mono ${isUrgent && item.status !== "completed" ? "text-red-400 font-bold" : "text-gray-400"}`}>
                          {item.date}
                        </p>
                        <p className="text-[10px] text-gray-600">
                          {isPast ? `${Math.abs(days)}d ago` : days === 0 ? "TODAY" : `in ${days}d`}
                        </p>
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className={`text-sm ${item.status === "completed" ? "text-gray-500 line-through" : "text-gray-200"}`}>
                            {item.title}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${STATUS_COLORS[item.status] || STATUS_COLORS.pending}`}>
                            {item.status}
                          </span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-500`}>
                            {item.type}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.description && <p className="text-[10px] text-gray-500 truncate">{item.description}</p>}
                          {item.assignee && <span className="text-[10px] text-gray-600">@{item.assignee}</span>}
                        </div>
                      </div>

                      {/* Delete */}
                      <button
                        onClick={() => onDelete(item.id)}
                        className="text-gray-700 hover:text-red-400 transition-colors shrink-0"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
