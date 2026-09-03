import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  Message,
  ProductClassificationMeta,
  ProductContextData,
  ClassificationState,
  ConversationSummary,
  ConversationDetail,
  Citation,
} from "@/types";
import { chatService, SendMessagePayload, VoiceChatResponse } from "@/services/chatService";
import { getWelcomeMessage, isWelcomeMessage } from "@/lib/welcomeLocalization";

export interface ChatMessage extends Message {
  citations?: Citation[];
  out_of_scope_detected?: boolean;
  product_classification?: ProductClassificationMeta;
}

const getInitialLang = (): string => {
  if (typeof window !== "undefined") {
    return localStorage.getItem("ip_sakti_lang") || "auto";
  }
  return "auto";
};

const createInitialWelcomeMessage = (lang: string = "auto"): ChatMessage => ({
  id: "welcome-msg",
  conversation_id: "init",
  role: "assistant",
  content: getWelcomeMessage(lang),
  jurisdiction: "INDIA",
  confidence_score: 1.0,
  confidence_label: "HIGH",
  requires_human_review: false,
  citations: [],
  created_at: new Date().toISOString(),
});

const DEFAULT_PRODUCT_CONTEXT: ProductContextData = {
  state: "PENDING",
  ingredients: [],
};

interface ChatState {
  activeConversationId: string | null;
  messages: ChatMessage[];
  productContext: ProductContextData | null;
  activeClassification: ProductClassificationMeta | null;
  classificationState: ClassificationState;
  conversations: ConversationSummary[];
  isLoadingHistory: boolean;
  isSending: boolean;
  isTranslating: boolean;
  isHistoryOpen: boolean;
  selectedLanguage: string;
  isVoiceContinuous: boolean;
  isSidebarCollapsed: boolean;

  // Setters
  setActiveConversationId: (id: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setProductContext: (context: ProductContextData | null) => void;
  setActiveClassification: (meta: ProductClassificationMeta | null) => void;
  setClassificationState: (state: ClassificationState) => void;
  toggleHistory: (open?: boolean) => void;
  setSelectedLanguage: (lang: string) => void;
  setIsTranslating: (translating: boolean) => void;
  setIsVoiceContinuous: (continuous: boolean) => void;
  setIsSidebarCollapsed: (collapsed: boolean) => void;

  // Actions
  fetchConversations: () => Promise<void>;
  startNewConsultation: () => void;
  loadConversation: (id: string) => Promise<void>;
  deleteConversation: (id: string) => Promise<void>;
  sendMessage: (payload: {
    query: string;
    jurisdiction: string;
    intent?: string;
  }) => Promise<void>;
  sendVoiceMessage: (
    audioBlob: Blob,
    jurisdiction: string,
    intent?: string
  ) => Promise<VoiceChatResponse>;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      activeConversationId: null,
      messages: [createInitialWelcomeMessage(getInitialLang())],
      productContext: DEFAULT_PRODUCT_CONTEXT,
      activeClassification: null,
      classificationState: "PENDING",
      conversations: [],
      isLoadingHistory: false,
      isSending: false,
      isTranslating: false,
      isHistoryOpen: false,
      selectedLanguage: getInitialLang(),
      isVoiceContinuous: false,
      isSidebarCollapsed: false,

      setActiveConversationId: (id) => set({ activeConversationId: id }),
      setMessages: (messages) => set({ messages }),
      setProductContext: (productContext) => set({ productContext }),
      setActiveClassification: (activeClassification) => set({ activeClassification }),
      setClassificationState: (classificationState) => set({ classificationState }),
      setIsVoiceContinuous: (isVoiceContinuous) => set({ isVoiceContinuous }),
      setIsSidebarCollapsed: (isSidebarCollapsed) => set({ isSidebarCollapsed }),
      setSelectedLanguage: (selectedLanguage) => {
        if (typeof window !== "undefined") {
          localStorage.setItem("ip_sakti_lang", selectedLanguage);
        }
        set((state) => {
          // If current conversation is unstarted / initial welcome message, dynamically update its text
          let updatedMessages = state.messages;
          if (
            state.activeConversationId === null &&
            state.messages.length === 1 &&
            state.messages[0].role === "assistant" &&
            isWelcomeMessage(state.messages[0].content)
          ) {
            updatedMessages = [
              {
                ...state.messages[0],
                content: getWelcomeMessage(selectedLanguage),
              },
            ];
          }
          return {
            selectedLanguage,
            messages: updatedMessages,
          };
        });
      },
      setIsTranslating: (isTranslating) => set({ isTranslating }),
      toggleHistory: (open) =>
        set((state) => ({
          isHistoryOpen: open !== undefined ? open : !state.isHistoryOpen,
        })),

      fetchConversations: async () => {
        set({ isLoadingHistory: true });
        try {
          const list = await chatService.getConversations();
          set({ conversations: list || [] });
        } catch (err) {
          console.error("Failed to fetch conversations", err);
        } finally {
          set({ isLoadingHistory: false });
        }
      },

      startNewConsultation: () => {
        const lang = get().selectedLanguage || getInitialLang();
        set({
          activeConversationId: null,
          messages: [
            {
              ...createInitialWelcomeMessage(lang),
              id: `welcome-${Date.now()}`,
              created_at: new Date().toISOString(),
            },
          ],
          productContext: DEFAULT_PRODUCT_CONTEXT,
          activeClassification: null,
          classificationState: "PENDING",
        });
      },

      loadConversation: async (convId: string) => {
        set({ isSending: true });
        try {
          const detail: ConversationDetail = await chatService.getConversation(convId);
          if (detail) {
            const formattedMessages: ChatMessage[] = (detail.messages || []).map((m) => ({
              id: m.id,
              conversation_id: m.conversation_id || convId,
              role: m.role,
              content: m.content,
              jurisdiction: m.jurisdiction,
              confidence_score: m.confidence_score,
              confidence_label: m.confidence_label,
              requires_human_review: m.requires_human_review,
              classification: m.classification,
              citations: m.citations || [],
              created_at: m.created_at || new Date().toISOString(),
            }));

            // If empty messages, supply default welcome
            const finalMessages =
              formattedMessages.length > 0
                ? formattedMessages
                : [
                    {
                      ...createInitialWelcomeMessage(get().selectedLanguage),
                      id: `welcome-${Date.now()}`,
                      created_at: detail.created_at,
                    },
                  ];

            const pContext = detail.product_context || {
              state: (detail.classification_state as ClassificationState) || "COLLECTING_PRODUCT_INFORMATION",
              ingredients: [],
            };

            const clState: ClassificationState =
              (detail.classification_state as ClassificationState) ||
              (pContext.state as ClassificationState) ||
              "COLLECTING_PRODUCT_INFORMATION";

            set({
              activeConversationId: detail.id,
              messages: finalMessages,
              productContext: pContext,
              activeClassification: detail.product_classification || null,
              classificationState: clState,
              isHistoryOpen: false,
            });
          }
        } catch (err) {
          console.error("Failed to load conversation details", err);
        } finally {
          set({ isSending: false });
        }
      },

      deleteConversation: async (convId: string) => {
        try {
          await chatService.deleteConversation(convId);
          const currentActive = get().activeConversationId;
          // Refresh list
          const updated = await chatService.getConversations();
          set({ conversations: updated || [] });

          // If the deleted session was currently active, reset to new consultation
          if (currentActive === convId) {
            get().startNewConsultation();
          }
        } catch (err) {
          console.error("Failed to delete conversation", err);
        }
      },

      sendMessage: async ({ query, jurisdiction, intent }) => {
        const state = get();
        const activeConvId = state.activeConversationId;
        const currentMessages = state.messages;
        const productContext = state.productContext;

        const userMsg: ChatMessage = {
          id: `usr-${Date.now()}`,
          conversation_id: activeConvId || "pending",
          role: "user",
          content: query,
          jurisdiction: jurisdiction,
          created_at: new Date().toISOString(),
        };

        // Append user message immediately
        set({
          messages: [...currentMessages, userMsg],
          isSending: true,
        });

        try {
          const payload: SendMessagePayload = {
            conversation_id: activeConvId || undefined,
            query: query,
            jurisdiction: jurisdiction,
            language: state.selectedLanguage || "auto",
            intent: intent,
            active_product_context: productContext ? JSON.stringify(productContext) : undefined,
          };

          const res = await chatService.sendMessage(payload);

          const botMsg: ChatMessage = {
            id: res.message_id || `bot-${Date.now()}`,
            conversation_id: res.conversation_id,
            role: "assistant",
            content: res.content,
            jurisdiction: res.jurisdiction,
            confidence_score: res.confidence_score,
            confidence_label: res.confidence_label,
            requires_human_review: res.requires_human_review,
            citations: res.citations || [],
            out_of_scope_detected: res.out_of_scope_detected,
            detected_language: res.detected_language,
            is_translated: res.is_translated,
            created_at: new Date().toISOString(),
          };

          // Synchronize updated product context and classification
          let newProductContext = state.productContext;
          let newClassification = state.activeClassification;
          let newClassificationState = state.classificationState;

          if (res.product_context) {
            newProductContext = res.product_context;
            if (res.product_context.state) {
              newClassificationState = res.product_context.state as ClassificationState;
            }
          }

          if (res.product_classification) {
            newClassification = res.product_classification;
          }

          set((s) => ({
            activeConversationId: res.conversation_id,
            messages: [...s.messages, botMsg],
            productContext: newProductContext,
            activeClassification: newClassification,
            classificationState: newClassificationState,
          }));

          // Refresh conversation list in background to update title / timestamps
          get().fetchConversations();
        } catch (err: any) {
          console.error("Chat turn error:", err);
          const errorMsg: ChatMessage = {
            id: `err-${Date.now()}`,
            conversation_id: activeConvId || "error",
            role: "assistant",
            content:
              "Unable to answer that at this moment. Please try again in a few moments or type your query in the text box.",
            jurisdiction: jurisdiction,
            requires_human_review: false,
            created_at: new Date().toISOString(),
          };
          set((s) => ({
            messages: [...s.messages, errorMsg],
          }));
        } finally {
          set({ isSending: false });
        }
      },

      sendVoiceMessage: async (
        audioBlob: Blob,
        jurisdiction: string,
        intent?: string
      ): Promise<VoiceChatResponse> => {
        const state = get();
        const activeConvId = state.activeConversationId;
        const productContext = state.productContext;

        set({ isSending: true });

        try {
          const formData = new FormData();
          formData.append("file", audioBlob, "speech_query.wav");
          if (activeConvId) formData.append("conversation_id", activeConvId);
          formData.append("jurisdiction", jurisdiction || "INDIA");
          formData.append("language", state.selectedLanguage || "auto");
          if (intent) formData.append("active_intent", intent);
          if (productContext) formData.append("active_product_context", JSON.stringify(productContext));

          const res = await chatService.sendVoiceMessage(formData);

          // Append recognized user speech turn and assistant response turn
          const userMsg: ChatMessage = {
            id: `usr-${Date.now()}`,
            conversation_id: res.conversation_id,
            role: "user",
            content: res.transcribed_text,
            jurisdiction: jurisdiction,
            created_at: new Date().toISOString(),
          };

          const botMsg: ChatMessage = {
            id: res.message_id || `bot-${Date.now()}`,
            conversation_id: res.conversation_id,
            role: "assistant",
            content: res.content,
            jurisdiction: res.jurisdiction,
            confidence_score: res.confidence_score,
            confidence_label: res.confidence_label,
            requires_human_review: res.requires_human_review,
            citations: res.citations || [],
            out_of_scope_detected: res.out_of_scope_detected,
            detected_language: res.detected_language,
            is_translated: res.is_translated,
            created_at: new Date().toISOString(),
          };

          let newProductContext = state.productContext;
          let newClassification = state.activeClassification;
          let newClassificationState = state.classificationState;

          if (res.product_context) {
            newProductContext = res.product_context;
            if (res.product_context.state) {
              newClassificationState = res.product_context.state as ClassificationState;
            }
          }

          if (res.product_classification) {
            newClassification = res.product_classification;
          }

          set((s) => ({
            activeConversationId: res.conversation_id,
            messages: [...s.messages, userMsg, botMsg],
            productContext: newProductContext,
            activeClassification: newClassification,
            classificationState: newClassificationState,
          }));

          get().fetchConversations();
          return res;
        } catch (err: any) {
          console.error("Voice chat turn error:", err);
          const errorMsg: ChatMessage = {
            id: `err-${Date.now()}`,
            conversation_id: activeConvId || "error",
            role: "assistant",
            content:
              "Unable to process voice message at this moment. Please try again or type your question in the text box.",
            jurisdiction: jurisdiction,
            requires_human_review: false,
            created_at: new Date().toISOString(),
          };
          set((s) => ({
            messages: [...s.messages, errorMsg],
          }));
          throw err;
        } finally {
          set({ isSending: false });
        }
      },
    }),
    {
      name: "ip-sakti-chat-session",
      partialize: (state) => ({
        activeConversationId: state.activeConversationId,
        messages: state.messages,
        productContext: state.productContext,
        activeClassification: state.activeClassification,
        classificationState: state.classificationState,
        selectedLanguage: state.selectedLanguage,
        isVoiceContinuous: state.isVoiceContinuous,
        isSidebarCollapsed: state.isSidebarCollapsed,
      }),
    }
  )
);
