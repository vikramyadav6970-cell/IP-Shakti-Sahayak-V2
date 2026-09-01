export type Role = "ADMIN" | "IP_FACILITATOR" | "CONTENT_MANAGER" | "RESEARCHER" | "USER";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  organization?: string;
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
}

export interface VectorCollectionStats {
  id: string;
  name: string;
  jurisdiction: string;
  description: string;
  official_authority: string;
  document_count: number;
}
