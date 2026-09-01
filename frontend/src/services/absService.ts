import { api } from "./apiClient";

export interface ABSAssessmentPayload {
  product_id?: string;
  entity_nationality: "INDIAN" | "FOREIGN" | "INDIAN_WITH_FOREIGN_EQUITY";
  biological_resources: string[];
  resource_origin: "INDIA" | "FOREIGN" | "BOTH";
  activity_type: "COMMERCIAL_UTILIZATION" | "RESEARCH" | "IPR_APPLICATION" | "TRANSFER_OF_RESULTS";
  is_ayush_practitioner?: boolean;
  is_codified_traditional_knowledge?: boolean;
  is_normally_traded_commodity?: boolean;
}

export interface ABSAssessmentResponse {
  id?: string;
  approval_required: boolean;
  approving_authority: string;
  form_type?: string;
  benefit_sharing_levy: string;
  relevance_label: string;
  statutory_provisions: string[];
  next_steps: string[];
  audit_notes: string[];
}

export const absService = {
  assess: async (payload: ABSAssessmentPayload): Promise<ABSAssessmentResponse> => {
    return await api.post<ABSAssessmentResponse>("/api/v1/abs", payload);
  },
};
