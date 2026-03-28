/**
 * API client for backend communication.
 */

import axios, { AxiosError, AxiosInstance } from "axios";
import { getToken, logout } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      logout();
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authApi = {
  register: async (data: {
    organization_name: string;
    full_name: string;
    email: string;
    password: string;
  }) => {
    const response = await api.post("/auth/register", data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post("/auth/login/json", { email, password });
    return response.data;
  },

  getMe: async () => {
    const response = await api.get("/auth/me");
    return response.data;
  },
};

// Project endpoints
export const projectsApi = {
  list: async () => {
    const response = await api.get("/projects/");
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  create: async (data: {
    name: string;
    client_name?: string;
    description?: string;
    bid_due_date?: string;
  }) => {
    const response = await api.post("/projects/", data);
    return response.data;
  },

  update: async (id: string, data: Partial<{
    name: string;
    client_name: string;
    description: string;
    bid_due_date: string;
    status: string;
  }>) => {
    const response = await api.patch(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/projects/${id}`);
  },
};

// Document endpoints
export const documentsApi = {
  upload: async (projectId: string, file: File) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("file", file);

    const response = await api.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },

  delete: async (id: string) => {
    await api.delete(`/documents/${id}`);
  },

  /** Download document and return blob URL for PDF viewer */
  getDocumentBlob: async (id: string): Promise<string> => {
    const response = await api.get(`/documents/${id}/download`, {
      responseType: "blob",
    });
    const blob = new Blob([response.data], { type: "application/pdf" });
    return URL.createObjectURL(blob);
  },

  /** Download document with highlighted text and return blob URL */
  getHighlightedDocumentBlob: async (
    id: string,
    searchText?: string,
    page?: number
  ): Promise<string> => {
    const params = new URLSearchParams();
    if (searchText) params.append("search_text", searchText);
    if (page) params.append("page", page.toString());

    const queryString = params.toString();
    const url = `/documents/${id}/download-highlighted${queryString ? `?${queryString}` : ""}`;

    const response = await api.get(url, {
      responseType: "blob",
    });
    const blob = new Blob([response.data], { type: "application/pdf" });
    return URL.createObjectURL(blob);
  },
};

// Analysis endpoints
export const analysisApi = {
  get: async (documentId: string) => {
    const response = await api.get(`/analysis/${documentId}`);
    return response.data;
  },

  getProjectAnalyses: async (projectId: string) => {
    const response = await api.get(`/analysis/project/${projectId}`);
    return response.data;
  },
};

// Billing endpoints
export const billingApi = {
  getPlans: async () => {
    const response = await api.get("/billing/plans");
    return response.data;
  },

  getSubscription: async () => {
    const response = await api.get("/billing/subscription");
    return response.data;
  },

  getUsage: async () => {
    const response = await api.get("/billing/usage");
    return response.data;
  },

  createCheckout: async (planTier: string, billingPeriod: string = "monthly") => {
    const response = await api.post("/billing/checkout", {
      plan_tier: planTier,
      billing_period: billingPeriod,
    });
    return response.data;
  },
};

// Organization endpoints
export const organizationApi = {
  getCurrent: async () => {
    const response = await api.get("/organizations/current");
    return response.data;
  },

  update: async (data: { name?: string }) => {
    const response = await api.patch("/organizations/current", data);
    return response.data;
  },

  getUsers: async () => {
    const response = await api.get("/organizations/current/users");
    return response.data;
  },
};

export default api;
