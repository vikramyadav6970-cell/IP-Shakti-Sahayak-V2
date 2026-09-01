import { ExpertRequestItem, User } from "../types";
import { useAdminAuthStore } from "../store/useAdminAuthStore";

const BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || "http://localhost:8000";

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = useAdminAuthStore.getState().token || localStorage.getItem("ip_sakti_admin_token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`, {
    ...options,
    headers: { ...headers, ...(options.headers as any) },
  });

  if (!response.ok) {
    let msg = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const data = await response.json();
      if (data?.detail) msg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch {}
    if (response.status === 401) {
      useAdminAuthStore.getState().clearAuth();
    }
    throw new Error(msg);
  }

  if (response.status === 204) return {} as T;
  return response.json();
}

export const adminService = {
  login: async (credentials: { email: string; password: string }): Promise<{ access_token: string }> => {
    return request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  },

  getMe: async (): Promise<User> => {
    return request<User>("/api/v1/users/me");
  },

  getQueue: async (statusFilter?: string): Promise<ExpertRequestItem[]> => {
    const query = statusFilter && statusFilter !== "ALL" ? `?status_filter=${statusFilter}` : "";
    return request<ExpertRequestItem[]>(`/api/v1/expert/queue${query}`);
  },

  resolveTicket: async (
    ticketId: string,
    payload: { status: "IN_PROGRESS" | "RESOLVED"; resolution_notes: string }
  ): Promise<ExpertRequestItem> => {
    return request<ExpertRequestItem>(`/api/v1/expert/${ticketId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },

  getSourcesOverview: async (): Promise<any> => {
    return request<any>("/api/v1/sources/overview");
  },
};
