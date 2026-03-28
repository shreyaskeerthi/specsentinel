"use client";

import React, { useState } from "react";

interface TeamMember {
  id: string;
  name: string;
  email: string | null;
  role: string;
  phone: string | null;
  invited: string;
}

const ROLES = ["Estimator", "PM", "Finance", "Ops", "Superintendent", "Executive"];

const ROLE_COLORS: Record<string, string> = {
  Estimator: "bg-blue-900/40 text-blue-400",
  PM: "bg-purple-900/40 text-purple-400",
  Finance: "bg-green-900/40 text-green-400",
  Ops: "bg-orange-900/40 text-orange-400",
  Superintendent: "bg-yellow-900/40 text-yellow-400",
  Executive: "bg-red-900/40 text-red-400",
};

interface TeamPanelProps {
  members: TeamMember[];
  onAdd: (member: { name: string; email?: string; role: string; phone?: string }) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
  onInvite: (id: string) => Promise<void>;
}

export default function TeamPanel({ members, onAdd, onRemove, onInvite }: TeamPanelProps) {
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", role: "Estimator", phone: "" });
  const [adding, setAdding] = useState(false);
  const [inviting, setInviting] = useState<string | null>(null);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    try {
      await onAdd({
        name: form.name,
        email: form.email || undefined,
        role: form.role,
        phone: form.phone || undefined,
      });
      setForm({ name: "", email: "", role: "Estimator", phone: "" });
      setShowAdd(false);
    } finally {
      setAdding(false);
    }
  };

  const handleInvite = async (id: string) => {
    setInviting(id);
    try {
      await onInvite(id);
    } finally {
      setInviting(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-400 uppercase">Project Team ({members.length})</h3>
        <button onClick={() => setShowAdd(!showAdd)} className="btn-primary text-sm">
          + Add Member
        </button>
      </div>

      {/* Add member form */}
      {showAdd && (
        <div className="card border-blue-800">
          <form onSubmit={handleAdd} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Name *</label>
                <input
                  required
                  value={form.name}
                  onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Jane Doe"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Role *</label>
                <select
                  value={form.role}
                  onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {ROLES.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-500 mb-1">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="jane@company.com"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-500 mb-1">Phone</label>
                <input
                  value={form.phone}
                  onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="(555) 123-4567"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" disabled={adding} className="btn-primary text-sm">{adding ? "Adding..." : "Add"}</button>
              <button type="button" onClick={() => setShowAdd(false)} className="btn-secondary text-sm">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Member list */}
      {members.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500">No team members yet. Add people to this project.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {members.map((m) => (
            <div key={m.id} className="card flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-gray-800 rounded-full flex items-center justify-center">
                  <span className="text-sm font-semibold text-gray-400">{m.name.charAt(0).toUpperCase()}</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-200">{m.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${ROLE_COLORS[m.role] || "bg-gray-800 text-gray-400"}`}>
                      {m.role}
                    </span>
                    {m.invited === "pending" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-900/30 text-yellow-400">Invited</span>
                    )}
                    {m.invited === "accepted" && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-900/30 text-green-400">Accepted</span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    {m.email && <span>{m.email}</span>}
                    {m.phone && <span>{m.phone}</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {m.email && m.invited === "no" && (
                  <button
                    onClick={() => handleInvite(m.id)}
                    disabled={inviting === m.id}
                    className="text-xs text-blue-400 hover:text-blue-300 px-2 py-1 rounded hover:bg-blue-900/20"
                  >
                    {inviting === m.id ? "Sending..." : "Invite"}
                  </button>
                )}
                <button
                  onClick={() => onRemove(m.id)}
                  className="text-xs text-red-500 hover:text-red-400 px-2 py-1 rounded hover:bg-red-900/20"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
