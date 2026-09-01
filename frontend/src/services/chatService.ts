import { api } from "./apiClient";
import {
  Citation,
  Feedback,
  ProductClassificationMeta,
  ProductContextData,
  ConversationSummary,
  ConversationDetail,
} from "@/types";

export interface SendMessagePayload {
  conversation_id?: string;
  query: string;
  jurisdiction: string;
  language?: string;
  intent?: string;
  active_product_context?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message_id: string;
  content: string;
  jurisdiction: string;
  confidence_score: number;
  confidence_label: "HIGH" | "MEDIUM" | "LOW";
  requires_human_review: boolean;
  citations: Citation[];
  out_of_scope_detected?: boolean;
  detected_jurisdiction?: string;
  detected_language?: string;
  original_language?: string;
  is_translated?: boolean;
  product_classification?: ProductClassificationMeta;
  product_context?: ProductContextData;
}

export const chatService = {
  sendMessage: async (payload: SendMessagePayload): Promise<ChatResponse> => {
    try {
      const q = payload.query || (payload as any).question || "";
      const body = {
        question: q,
        query: q,
        jurisdiction: payload.jurisdiction || "INDIA",
        language: payload.language || "auto",
        conversation_id: payload.conversation_id,
        active_intent: payload.intent,
        active_product_context: payload.active_product_context,
      };
      return await api.post<ChatResponse>("/api/v1/chat", body);
    } catch {
      // Offline / Pre-Phase-3 Mock response for UI testing
      const isOutScope =
        (payload.jurisdiction === "INDIA" && /uspto|fda|epo|trips|nagoya/i.test(payload.query)) ||
        (payload.jurisdiction === "INTERNATIONAL" && /section 3\(p\)|bda|form i\b|fssai/i.test(payload.query));

      if (isOutScope) {
        return {
          conversation_id: payload.conversation_id || "mock-conv-id",
          message_id: "msg-out-scope",
          content: "The inquiry targets a different legal jurisdiction from your active session.",
          jurisdiction: payload.jurisdiction,
          confidence_score: 0.95,
          confidence_label: "HIGH",
          requires_human_review: false,
          citations: [],
          out_of_scope_detected: true,
          detected_jurisdiction: payload.jurisdiction === "INDIA" ? "INTERNATIONAL" : "INDIA",
        };
      }

      const isClassifyIntent = /classify|formulation|recipe|extract|herb|cream|aahara|guggulu|churna|ashwagandha/i.test(payload.query);
      let product_classification: ProductClassificationMeta | undefined = undefined;
      let product_context: ProductContextData | undefined = undefined;

      if (isClassifyIntent && /triphala|churna|classical/i.test(payload.query)) {
        product_classification = {
          category: "CLASSICAL_MEDICINE",
          category_name: "Classical / Generic Medicine",
          product_name: "Classical Triphala Churna",
          regulatory_pathway: "Form 25-D AYUSH Manufacturing License under Rule 153.",
          statutory_authority: "Drugs & Cosmetics Act 1940 & Rules 1945",
          reasoning: "Formulation and method drawn verbatim from an authoritative First-Schedule classical text.",
          patent_eligibility: "EXCLUDED",
          patent_reasoning: "Excluded under Section 3(p) of the Patents Act 1970 (Traditional Knowledge).",
          abs_requirement: "SBB Prior Intimation required for commercial manufacture in India.",
          confidence: 0.96,
        };
        product_context = {
          product_name: "Classical Triphala Churna",
          description: "Traditional herbal churna preparation",
          formulation: "Fine powder prepared per Ayurvedic Formulary of India",
          ingredients: ["Terminalia chebula (Haritaki)", "Terminalia bellerica (Bibhitaki)", "Emblica officinalis (Amalaki)"],
          dosage_form: "Churna / Powder",
          intended_use: "Digestive and metabolic wellness",
          classical_source: "Ayurvedic Formulary of India (AFI)",
          state: "CLASSIFIED",
          category: "Classical / Generic Medicine",
          category_name: "Classical / Generic Medicine",
          classification_reason: "Drawn verbatim from First-Schedule text.",
          regulatory_pathway: "Form 25-D AYUSH License",
          statutory_authority: "Drugs & Cosmetics Act 1940",
          patent_eligibility: "EXCLUDED",
        };
      } else if (isClassifyIntent) {
        product_context = {
          description: payload.query,
          state: "COLLECTING_PRODUCT_INFORMATION",
        };
      }

      const isLegalRAGQuery = /patent|section 3|abs|nba|treaty|fssai|statute|infringement|prior art|court|act/i.test(payload.query);
      const citations: Citation[] = isLegalRAGQuery
        ? (payload.jurisdiction === "INDIA"
            ? [
                {
                  id: "cit-1",
                  message_id: "msg-1",
                  document_title: "The Patents Act, 1970 (as amended)",
                  section_ref: "Section 3(p)",
                  source_url: "https://wipolex.wipo.int/en/legislation/details/2143",
                  jurisdiction: "INDIA",
                  document_type: "STATUTE",
                  verification_status: "VERIFIED_OFFICIAL_GAZETTE",
                },
                {
                  id: "cit-2",
                  message_id: "msg-1",
                  document_title: "The Biological Diversity Act, 2002 & 2023",
                  section_ref: "Section 3 / Form I",
                  source_url: "https://indiacode.nic.in/handle/123456789/2145",
                  jurisdiction: "INDIA",
                  document_type: "STATUTE",
                  verification_status: "VERIFIED_OFFICIAL_GAZETTE",
                },
              ]
            : [
                {
                  id: "cit-intl-1",
                  message_id: "msg-1",
                  document_title: "TRIPS Agreement (WTO)",
                  section_ref: "Article 27.1 & 27.2",
                  source_url: "https://wipolex.wipo.int/en/treaties/details/231",
                  jurisdiction: "INTERNATIONAL",
                  document_type: "TREATY",
                  verification_status: "VERIFIED_OFFICIAL_TREATY",
                },
              ])
        : [];

      return {
        conversation_id: payload.conversation_id || "mock-conv-id",
        message_id: "mock-msg-response",
        content: `Under ${payload.jurisdiction === "INDIA" ? "Indian Patent Law (Patents Act 1970 §3(p))" : "International Treaties (TRIPS Art 27)"}, traditional Ayurvedic knowledge and mere admixture of known herbs without synergistic efficacy are excluded from patentability. However, novel standardized extraction methods, synergistic combinations with demonstrated bio-enhancement, and distinctive trademarks under Class 5 are legally protectable.`,
        jurisdiction: payload.jurisdiction,
        confidence_score: 0.94,
        confidence_label: "HIGH",
        requires_human_review: false,
        citations,
        product_classification,
        product_context,
      };
    }
  },

  getConversations: async (): Promise<ConversationSummary[]> => {
    try {
      return await api.get<ConversationSummary[]>("/api/v1/chat/conversations");
    } catch {
      return [];
    }
  },

  getConversation: async (id: string): Promise<ConversationDetail> => {
    return await api.get<ConversationDetail>(`/api/v1/chat/conversations/${id}`);
  },

  deleteConversation: async (id: string): Promise<void> => {
    await api.delete(`/api/v1/chat/conversations/${id}`);
  },

  submitFeedback: async (messageId: string, rating: number, comment?: string): Promise<Feedback> => {
    try {
      return await api.post<Feedback>(`/api/v1/chat/${messageId}/feedback`, { rating, comment });
    } catch {
      return {
        id: "mock-feedback-id",
        message_id: messageId,
        user_id: "mock-user",
        rating,
        comment,
        created_at: new Date().toISOString(),
      };
    }
  },
};
