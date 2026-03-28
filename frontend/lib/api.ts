/**
 * API client for SpecSentinel v2 — with auth.
 */

import axios from "axios";
import { getToken, logout } from "./auth";
import type { AnalysisResult, EmailSet, MeetingAnalysis } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const api = axios.create({ baseURL: `${API_BASE}/api` });

// Attach token
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      logout();
    }
    return Promise.reject(err);
  }
);

// ── Auth ──

export async function register(data: { email: string; password: string; full_name: string; company?: string }) {
  const { data: res } = await api.post("/auth/register", data);
  return res;
}

export async function login(email: string, password: string) {
  const { data: res } = await api.post("/auth/login", { email, password });
  return res;
}

export async function getMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

// ── Projects ──

export async function listProjects() {
  const { data } = await api.get("/projects");
  return data;
}

export async function createProject(data: {
  name: string;
  client_name?: string;
  description?: string;
  bid_due_date?: string;
  contract_value?: number;
  budget?: number;
}) {
  const { data: res } = await api.post("/projects", data);
  return res;
}

export async function getProject(id: string) {
  const { data } = await api.get(`/projects/${id}`);
  return data;
}

export async function updateProject(id: string, data: any) {
  const { data: res } = await api.patch(`/projects/${id}`, data);
  return res;
}

export async function deleteProject(id: string) {
  await api.delete(`/projects/${id}`);
}

// ── Team ──

export async function addTeamMember(projectId: string, data: { name: string; email?: string; role: string; phone?: string }) {
  const { data: res } = await api.post(`/projects/${projectId}/team`, data);
  return res;
}

export async function updateTeamMember(projectId: string, memberId: string, data: any) {
  const { data: res } = await api.patch(`/projects/${projectId}/team/${memberId}`, data);
  return res;
}

export async function removeTeamMember(projectId: string, memberId: string) {
  await api.delete(`/projects/${projectId}/team/${memberId}`);
}

export async function inviteTeamMember(projectId: string, memberId: string) {
  const { data } = await api.post(`/projects/${projectId}/team/${memberId}/invite`);
  return data;
}

// ── Milestones ──

export async function createMilestone(projectId: string, data: {
  title: string; date: string; phase: string; type?: string; description?: string; assignee?: string;
}) {
  const { data: res } = await api.post(`/projects/${projectId}/milestones`, data);
  return res;
}

export async function updateMilestone(projectId: string, milestoneId: string, data: any) {
  const { data: res } = await api.patch(`/projects/${projectId}/milestones/${milestoneId}`, data);
  return res;
}

export async function deleteMilestone(projectId: string, milestoneId: string) {
  await api.delete(`/projects/${projectId}/milestones/${milestoneId}`);
}

// ── Upload (async — returns immediately) ──

export async function uploadSpec(projectId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post(`/projects/${projectId}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data; // { analysis_id, status: "pending" }
}

// ── Analysis (poll this) ──

export async function getAnalysis(id: string) {
  const { data } = await api.get(`/analysis/${id}`);
  return data;
}

/** Poll until analysis is done. Calls onStatus for progress. */
export async function pollAnalysis(
  analysisId: string,
  onStatus?: (status: string) => void,
  intervalMs: number = 2000,
): Promise<any> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const result = await getAnalysis(analysisId);
        onStatus?.(result.status);
        if (result.status === "completed") {
          resolve(result);
        } else if (result.status === "failed") {
          reject(new Error(result.error_message || "Analysis failed"));
        } else {
          setTimeout(poll, intervalMs);
        }
      } catch (err) {
        reject(err);
      }
    };
    poll();
  });
}

// ── Meeting Notes ──

export async function analyzeMeetingNotes(projectId: string, notes: string) {
  const { data } = await api.post(`/projects/${projectId}/meeting-notes`, { notes });
  return data; // { analysis_id, status: "pending" }
}

// ── Emails ──

export async function generateEmails(analysisId: string): Promise<EmailSet> {
  const { data } = await api.post(`/analysis/${analysisId}/generate-emails`);
  return data;
}

export async function sendEmail(email: any) {
  const { data } = await api.post("/send-email", email);
  return data;
}
