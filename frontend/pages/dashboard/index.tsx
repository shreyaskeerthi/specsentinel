/**
 * Main dashboard - list of projects.
 */

import React, { useEffect, useState } from "react";
import Head from "next/head";
import Layout from "@/components/Layout";
import ProjectCard from "@/components/ProjectCard";
import Modal from "@/components/Modal";
import { projectsApi } from "@/lib/api";
import type { ProjectListItem } from "@/lib/types";

export default function DashboardPage() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProject, setNewProject] = useState({
    name: "",
    client_name: "",
    bid_due_date: "",
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await projectsApi.list();
      setProjects(data);
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setCreating(true);

    try {
      await projectsApi.create({
        name: newProject.name,
        client_name: newProject.client_name || undefined,
        bid_due_date: newProject.bid_due_date || undefined,
      });
      setShowNewProject(false);
      setNewProject({ name: "", client_name: "", bid_due_date: "" });
      loadProjects();
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  return (
    <Layout requireAuth>
      <Head>
        <title>Dashboard - SpecSentinel</title>
      </Head>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
            <p className="text-gray-600">Manage your bid opportunities and spec analyses</p>
          </div>
          <button
            onClick={() => setShowNewProject(true)}
            className="btn-primary"
          >
            + New Project
          </button>
        </div>

        {/* Projects Grid */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12 card">
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-gray-500 mb-4">
              Create your first project to start analyzing spec documents.
            </p>
            <button
              onClick={() => setShowNewProject(true)}
              className="btn-primary"
            >
              Create Project
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        )}

        {/* New Project Modal */}
        <Modal
          isOpen={showNewProject}
          onClose={() => setShowNewProject(false)}
          title="Create New Project"
        >
          <form onSubmit={handleCreateProject} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Project Name *
              </label>
              <input
                id="name"
                type="text"
                required
                value={newProject.name}
                onChange={(e) => setNewProject((prev) => ({ ...prev, name: e.target.value }))}
                className="input"
                placeholder="e.g., City Hall HVAC Renovation"
              />
            </div>

            <div>
              <label htmlFor="client_name" className="block text-sm font-medium text-gray-700 mb-1">
                Client Name
              </label>
              <input
                id="client_name"
                type="text"
                value={newProject.client_name}
                onChange={(e) => setNewProject((prev) => ({ ...prev, client_name: e.target.value }))}
                className="input"
                placeholder="e.g., City of Springfield"
              />
            </div>

            <div>
              <label htmlFor="bid_due_date" className="block text-sm font-medium text-gray-700 mb-1">
                Bid Due Date
              </label>
              <input
                id="bid_due_date"
                type="date"
                value={newProject.bid_due_date}
                onChange={(e) => setNewProject((prev) => ({ ...prev, bid_due_date: e.target.value }))}
                className="input"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={() => setShowNewProject(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={creating}
                className="btn-primary"
              >
                {creating ? "Creating..." : "Create Project"}
              </button>
            </div>
          </form>
        </Modal>
      </div>
    </Layout>
  );
}
