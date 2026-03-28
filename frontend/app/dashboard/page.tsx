"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { listProjects, createProject } from "@/lib/api";
import { isAuthenticated, getUser, logout } from "@/lib/auth";

function formatCurrency(n: number | null | undefined): string {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
}

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", client_name: "", bid_due_date: "", contract_value: "", budget: "" });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const user = getUser();

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    loadProjects();
  }, [router]);

  const loadProjects = useCallback(async () => {
    try {
      const data = await listProjects();
      setProjects(data);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    setError("");
    try {
      const project = await createProject({
        name: form.name,
        client_name: form.client_name || undefined,
        bid_due_date: form.bid_due_date || undefined,
        contract_value: form.contract_value ? parseFloat(form.contract_value) : undefined,
        budget: form.budget ? parseFloat(form.budget) : undefined,
      });
      setShowCreate(false);
      setForm({ name: "", client_name: "", bid_due_date: "", contract_value: "", budget: "" });
      router.push(`/projects/${project.id}`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const STATUS_COLORS: Record<string, string> = {
    active: "bg-blue-900/40 text-blue-400",
    won: "bg-green-900/40 text-green-400",
    lost: "bg-red-900/40 text-red-400",
    no_bid: "bg-gray-800 text-gray-400",
    archived: "bg-gray-800 text-gray-500",
  };

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SS</span>
            </div>
            <span className="text-lg font-bold text-white">SpecSentinel</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{user?.full_name}</span>
            <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300">Sign out</button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-white">Projects</h1>
            <p className="text-gray-500 text-sm">Manage bids and analyze specs</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="btn-primary">+ New Project</button>
        </div>

        {/* Create modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
            <div className="card w-full max-w-lg" onClick={(e) => e.stopPropagation()}>
              <h2 className="text-lg font-semibold text-white mb-4">New Project</h2>
              {error && <div className="bg-red-900/30 border border-red-800 text-red-400 px-3 py-2 rounded-lg text-sm mb-3">{error}</div>}
              <form onSubmit={handleCreate} className="space-y-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Project Name *</label>
                  <input required value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="City Hall HVAC Renovation" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Client</label>
                  <input value={form.client_name} onChange={(e) => setForm((p) => ({ ...p, client_name: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="City of Springfield" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Bid Due Date</label>
                    <input type="date" value={form.bid_due_date} onChange={(e) => setForm((p) => ({ ...p, bid_due_date: e.target.value }))}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">Contract Value ($)</label>
                    <input type="number" step="1000" value={form.contract_value} onChange={(e) => setForm((p) => ({ ...p, contract_value: e.target.value }))}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="2,500,000" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Internal Budget ($)</label>
                  <input type="number" step="1000" value={form.budget} onChange={(e) => setForm((p) => ({ ...p, budget: e.target.value }))}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="2,200,000" />
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                  <button type="submit" disabled={creating} className="btn-primary">{creating ? "Creating..." : "Create"}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Project list */}
        {loading ? (
          <p className="text-gray-500 text-center py-12">Loading...</p>
        ) : projects.length === 0 ? (
          <div className="card text-center py-12">
            <h3 className="text-lg text-gray-300 mb-2">No projects yet</h3>
            <p className="text-gray-500 mb-4">Create your first project to start analyzing specs.</p>
            <button onClick={() => setShowCreate(true)} className="btn-primary">Create Project</button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <div
                key={p.id}
                onClick={() => router.push(`/projects/${p.id}`)}
                className="card cursor-pointer hover:border-gray-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white">{p.name}</h3>
                    {p.client_name && <p className="text-sm text-gray-400">{p.client_name}</p>}
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[p.status] || STATUS_COLORS.active}`}>
                    {p.status}
                  </span>
                </div>

                {/* Money row */}
                <div className="flex items-center gap-4 mb-3">
                  {p.contract_value && (
                    <div>
                      <p className="text-[10px] text-gray-600 uppercase">Contract</p>
                      <p className="text-sm font-semibold text-green-400">{formatCurrency(p.contract_value)}</p>
                    </div>
                  )}
                  {p.budget && (
                    <div>
                      <p className="text-[10px] text-gray-600 uppercase">Budget</p>
                      <p className="text-sm font-semibold text-blue-400">{formatCurrency(p.budget)}</p>
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-3 text-xs text-gray-500">
                  <span>{p.document_count} doc{p.document_count !== 1 ? "s" : ""}</span>
                  <span>{p.team_count} member{p.team_count !== 1 ? "s" : ""}</span>
                  {p.bid_due_date && <span>Due: {p.bid_due_date}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
