"use client";

import React, { useState, useMemo } from "react";
import type { ActionTask, ScheduleEvent } from "@/lib/types";

interface CalendarProps {
  tasks: ActionTask[];
  scheduleEvents: ScheduleEvent[];
  bidDueDate?: string | null;
  teamMembers: { id: string; name: string; email: string | null; role: string }[];
  onAddEvent: (event: { title: string; date: string; type: string; description: string }) => void;
  onSendSchedule: (memberIds: string[]) => void;
}

const EVENT_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  deadline: { bg: "bg-red-900/30", text: "text-red-400", dot: "bg-red-500" },
  milestone: { bg: "bg-blue-900/30", text: "text-blue-400", dot: "bg-blue-500" },
  task: { bg: "bg-purple-900/30", text: "text-purple-400", dot: "bg-purple-500" },
  blackout: { bg: "bg-orange-900/30", text: "text-orange-400", dot: "bg-orange-500" },
  meeting: { bg: "bg-green-900/30", text: "text-green-400", dot: "bg-green-500" },
};

function formatDate(d: string): string {
  try {
    return new Date(d + "T00:00:00").toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  } catch { return d; }
}

function daysUntil(d: string): number {
  const target = new Date(d + "T00:00:00");
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return Math.ceil((target.getTime() - now.getTime()) / 86400000);
}

export default function Calendar({ tasks, scheduleEvents, bidDueDate, teamMembers, onAddEvent, onSendSchedule }: CalendarProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [showSend, setShowSend] = useState(false);
  const [selectedMembers, setSelectedMembers] = useState<Set<string>>(new Set());
  const [sent, setSent] = useState(false);
  const [newEvent, setNewEvent] = useState({ title: "", date: "", type: "task", description: "" });

  // Combine all dated items into a timeline
  const timeline = useMemo(() => {
    const items: { date: string; title: string; type: string; description: string | null; source: string; priority?: string; assignee?: string | null; status?: string }[] = [];

    // Add schedule events from meeting notes
    for (const ev of scheduleEvents) {
      if (ev.date) items.push({ ...ev, source: "meeting" });
    }

    // Add tasks with due dates
    for (const task of tasks) {
      if (task.due_date) {
        items.push({
          date: task.due_date,
          title: task.title,
          type: "task",
          description: task.description,
          source: "actionboard",
          priority: task.priority,
          assignee: task.assignee,
          status: task.status,
        });
      }
    }

    // Add bid due date
    if (bidDueDate) {
      items.push({ date: bidDueDate, title: "BID DUE DATE", type: "deadline", description: "Bid submission deadline", source: "project" });
    }

    // Sort by date
    items.sort((a, b) => a.date.localeCompare(b.date));
    return items;
  }, [tasks, scheduleEvents, bidDueDate]);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEvent.title || !newEvent.date) return;
    onAddEvent(newEvent);
    setNewEvent({ title: "", date: "", type: "task", description: "" });
    setShowAdd(false);
  };

  const handleSend = () => {
    onSendSchedule(Array.from(selectedMembers));
    setSent(true);
    setTimeout(() => { setSent(false); setShowSend(false); }, 2000);
  };

  return (
    <div className="space-y-4">
      {/* Header with actions */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">
          Project Schedule ({timeline.length} events)
        </h3>
        <div className="flex gap-2">
          <button onClick={() => setShowAdd(!showAdd)} className="btn-secondary text-sm">+ Add Event</button>
          <button onClick={() => setShowSend(!showSend)} className="btn-primary text-sm">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Send Schedule
            </span>
          </button>
        </div>
      </div>

      {/* Add event form */}
      {showAdd && (
        <div className="card border-blue-800">
          <form onSubmit={handleAdd} className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Title *</label>
                <input required value={newEvent.title} onChange={(e) => setNewEvent((p) => ({ ...p, title: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Equipment delivery" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Date *</label>
                <input type="date" required value={newEvent.date} onChange={(e) => setNewEvent((p) => ({ ...p, date: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Type</label>
                <select value={newEvent.type} onChange={(e) => setNewEvent((p) => ({ ...p, type: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500">
                  <option value="task">Task</option>
                  <option value="deadline">Deadline</option>
                  <option value="milestone">Milestone</option>
                  <option value="blackout">Blackout</option>
                  <option value="meeting">Meeting</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Description</label>
              <input value={newEvent.description} onChange={(e) => setNewEvent((p) => ({ ...p, description: e.target.value }))}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Optional details" />
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn-primary text-sm">Add</button>
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary text-sm">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Send schedule panel */}
      {showSend && (
        <div className="card border-blue-800">
          <h4 className="text-sm font-medium text-gray-300 mb-2">Send schedule to team members</h4>
          {teamMembers.length === 0 ? (
            <p className="text-sm text-gray-500">No team members with email addresses. Add team members first.</p>
          ) : (
            <>
              <div className="space-y-1 mb-3">
                {teamMembers.map((m) => (
                  <label key={m.id} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:bg-gray-800/50 rounded px-2 py-1">
                    <input
                      type="checkbox"
                      checked={selectedMembers.has(m.id)}
                      onChange={(e) => {
                        const next = new Set(selectedMembers);
                        e.target.checked ? next.add(m.id) : next.delete(m.id);
                        setSelectedMembers(next);
                      }}
                      className="rounded border-gray-600"
                    />
                    {m.name} <span className="text-gray-500">({m.role})</span>
                    {m.email && <span className="text-gray-600 text-xs">{m.email}</span>}
                  </label>
                ))}
              </div>
              <button
                onClick={handleSend}
                disabled={selectedMembers.size === 0 || sent}
                className="btn-primary text-sm"
              >
                {sent ? "Sent!" : `Send to ${selectedMembers.size} member${selectedMembers.size !== 1 ? "s" : ""}`}
              </button>
            </>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="flex gap-3 flex-wrap">
        {Object.entries(EVENT_COLORS).map(([type, colors]) => (
          <span key={type} className="flex items-center gap-1.5 text-xs text-gray-500">
            <span className={`w-2 h-2 rounded-full ${colors.dot}`} />
            {type}
          </span>
        ))}
      </div>

      {/* Timeline */}
      {timeline.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500">No scheduled events yet.</p>
          <p className="text-gray-600 text-sm mt-1">Analyze meeting notes or add events manually to build the schedule.</p>
        </div>
      ) : (
        <div className="space-y-1">
          {timeline.map((item, i) => {
            const colors = EVENT_COLORS[item.type] || EVENT_COLORS.task;
            const days = daysUntil(item.date);
            const isPast = days < 0;
            const isUrgent = days >= 0 && days <= 3;

            return (
              <div key={i} className={`flex items-start gap-3 rounded-lg border border-gray-800 px-4 py-3 ${colors.bg} ${isPast ? "opacity-50" : ""}`}>
                {/* Date column */}
                <div className="w-24 shrink-0 text-right">
                  <p className={`text-sm font-mono ${colors.text}`}>{formatDate(item.date)}</p>
                  <p className={`text-[10px] ${isUrgent ? "text-red-400 font-bold" : "text-gray-600"}`}>
                    {isPast ? `${Math.abs(days)}d ago` : days === 0 ? "TODAY" : `in ${days}d`}
                  </p>
                </div>

                {/* Dot */}
                <div className="flex flex-col items-center pt-1.5">
                  <span className={`w-2.5 h-2.5 rounded-full ${colors.dot}`} />
                  {i < timeline.length - 1 && <div className="w-px h-6 bg-gray-800 mt-1" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${item.type === "deadline" ? "text-red-300 font-bold" : "text-gray-200"}`}>
                      {item.title}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text} border border-current/20`}>
                      {item.type}
                    </span>
                    {(item as any).assignee && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-800 text-gray-400">
                        {(item as any).assignee}
                      </span>
                    )}
                    {(item as any).priority && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        (item as any).priority === "high" ? "bg-red-900/30 text-red-400" :
                        (item as any).priority === "medium" ? "bg-yellow-900/30 text-yellow-400" :
                        "bg-green-900/30 text-green-400"
                      }`}>
                        {(item as any).priority}
                      </span>
                    )}
                  </div>
                  {item.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{item.description}</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
