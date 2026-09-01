import { api } from "./apiClient";

export interface ExpertEscalatePayload {
  message_id?: string;
  issue_description: string;
  urgency_level?: "NORMAL" | "HIGH" | "URGENT";
}

export interface ExpertRequestItem {
  id: string;
  user_id: string;
  message_id?: string;
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED";
  context: string;
  response?: string;
  resolved_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ExpertResolvePayload {
  status: "OPEN" | "IN_PROGRESS" | "RESOLVED";
  resolution_notes: string;
}

export const expertService = {
  escalate: async (payload: ExpertEscalatePayload): Promise<ExpertRequestItem> => {
    return await api.post<ExpertRequestItem>("/api/v1/expert/escalate", payload);
  },
  getMyRequests: async (): Promise<ExpertRequestItem[]> => {
    return await api.get<ExpertRequestItem[]>("/api/v1/expert/my-requests");
  },
  getMyRequestById: async (id: string): Promise<ExpertRequestItem> => {
    return await api.get<ExpertRequestItem>(`/api/v1/expert/my-requests/${id}`);
  },
  getQueue: async (): Promise<ExpertRequestItem[]> => {
    return await api.get<ExpertRequestItem[]>("/api/v1/expert/queue");
  },
  resolve: async (id: string, payload: ExpertResolvePayload): Promise<ExpertRequestItem> => {
    return await api.patch<ExpertRequestItem>(`/api/v1/expert/${id}`, payload);
  },
};
