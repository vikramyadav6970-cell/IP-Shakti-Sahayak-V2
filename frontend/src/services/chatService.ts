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
  domain_confidence?: Record<string, any>;
}

export interface VoiceChatResponse extends ChatResponse {
  transcribed_text: string;
  audio_base64?: string | null;
  audio_format?: string;
}

export const chatService = {
  sendMessage: async (payload: SendMessagePayload): Promise<ChatResponse> => {
    try {
      const q = payload.query || (payload as any).question || "";
      const body: Record<string, any> = {
        question: q,
        query: q,
        jurisdiction: payload.jurisdiction || "INDIA",
        language: payload.language || "auto",
      };

      if (payload.conversation_id && payload.conversation_id !== "mock-conv-id") {
        body.conversation_id = payload.conversation_id;
      }
      if (payload.intent) {
        body.active_intent = payload.intent;
      }
      if (payload.active_product_context) {
        body.active_product_context = payload.active_product_context;
      }

      return await api.post<ChatResponse>("/api/v1/chat", body);
    } catch (error) {
      console.error("[Live Chat API Error]:", error);
      throw error;
    }
  },

  sendVoiceMessage: async (formData: FormData): Promise<VoiceChatResponse> => {
    return await api.postForm<VoiceChatResponse>("/api/v1/chat/voice", formData);
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
