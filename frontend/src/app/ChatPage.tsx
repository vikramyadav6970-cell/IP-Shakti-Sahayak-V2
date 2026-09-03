import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  Send,
  Loader2,
  Scale,
  HelpCircle,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  Plus,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  Trash2,
  Languages,
  BookOpen,
  Sparkles,
} from "lucide-react";
import { useJurisdiction } from "@/store/useJurisdictionStore";
import { useChatStore, ChatMessage } from "@/store/useChatStore";
import { chatService } from "@/services/chatService";
import { ConfidenceBadge } from "@/components/chat/ConfidenceBadge";
import { JurisdictionOutGuardrail } from "@/components/chat/JurisdictionOutGuardrail";
import { ExpertEscalationModal } from "@/components/chat/ExpertEscalationModal";
import { ProductClassificationPanel } from "@/components/chat/ProductClassificationPanel";
import { LanguageSelector } from "@/components/chat/LanguageSelector";
import { VoiceInputButton } from "@/components/chat/VoiceInputButton";
import { VoiceConversationButton } from "@/components/chat/VoiceConversationButton";
import {
  getSampleQueries,
  getSampleQueriesHeading,
  isWelcomeMessage,
} from "@/lib/welcomeLocalization";

export const ChatPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const initialIntent = searchParams.get("intent") || "";

  const [input, setInput] = useState(initialQuery);
  const [escalateModalOpen, setEscalateModalOpen] = useState(false);
  const [selectedMessageId, setSelectedMessageId] = useState<string | undefined>(undefined);
  const [showClassifier, setShowClassifier] = useState(true);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, number>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { primary, setPrimary, active } = useJurisdiction();

  // Zustand Store
  const {
    messages,
    productContext,
    activeClassification,
    classificationState,
    conversations,
    activeConversationId,
    isSending,
    selectedLanguage,
    isSidebarCollapsed,
    sendMessage,
    startNewConsultation,
    loadConversation,
    deleteConversation,
    fetchConversations,
    setIsSidebarCollapsed,
    setActiveClassification,
    setProductContext,
    setClassificationState,
  } = useChatStore();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Execute initial query if provided via URL params
  useEffect(() => {
    if (initialQuery && messages.length === 1 && isWelcomeMessage(messages[0].content)) {
      handleSendMessage(initialQuery);
    }
  }, [initialQuery]);

  const handleSendMessage = async (queryText: string) => {
    if (!queryText.trim() || isSending) return;
    setInput("");
    await sendMessage({
      query: queryText,
      jurisdiction: active || primary || "INDIA",
      intent: initialIntent || undefined,
    });
  };

  const handleStartDiagnostic = () => {
    startNewConsultation();
  };

  const handleResetClassification = () => {
    setActiveClassification(null);
    setProductContext({
      state: "COLLECTING_PRODUCT_INFORMATION",
      ingredients: [],
    });
    setClassificationState("COLLECTING_PRODUCT_INFORMATION");
  };

  const handleFeedback = async (messageId: string, rating: number) => {
    setFeedbackMap((prev) => ({ ...prev, [messageId]: rating }));
    try {
      await chatService.submitFeedback(messageId, rating);
    } catch (err) {
      console.error("Failed to submit feedback", err);
    }
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm("Delete this consultation session?")) {
      await deleteConversation(id);
    }
  };

  return (
    <div
      className="h-full w-full p-2 sm:p-3 rounded-2xl glass-page-bg transition-all flex flex-col overflow-hidden min-h-0"
      style={{
        background: `
          radial-gradient(circle at 15% 15%, var(--bg-blob-1, #D7F5E5) 0%, transparent 45%),
          radial-gradient(circle at 85% 85%, var(--bg-blob-2, #DCF0E0) 0%, transparent 45%),
          var(--bg-page, #F3F8F5)
        `,
      }}
    >
      {/* Workspace: Collapsible Sidebar + Main Chat Panel */}
      <div className="flex flex-col lg:flex-row gap-3 items-stretch w-full flex-1 min-h-0 overflow-hidden">
        {/* =========================================================================
            1. Collapsible Left Sidebar (30% Classifier Diagnostic + 70% History)
            ========================================================================= */}
        <aside
          aria-label="Sidebar Workspace"
          className={`shrink-0 flex flex-col justify-between transition-all duration-200 ease-in-out rounded-2xl glass-panel-card h-full min-h-0 overflow-hidden ${
            isSidebarCollapsed ? "w-12 p-2 items-center" : "w-full lg:w-64 xl:w-72 p-2.5"
          }`}
        >
          {isSidebarCollapsed ? (
            /* Collapsed Rail (Icon-only, clean without list or scrollbars) */
            <div className="w-full flex flex-col items-center gap-2 pt-1">
              <button
                type="button"
                onClick={() => setIsSidebarCollapsed(false)}
                className="p-1.5 rounded-lg hover:bg-white/80 transition-colors"
                style={{ color: "var(--accent-600, #059669)" }}
                title="Expand Sidebar"
              >
                <PanelLeftOpen className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={startNewConsultation}
                className="p-1.5 rounded-lg hover:bg-white/80 transition-colors"
                style={{ color: "var(--accent-600, #059669)" }}
                title="New Consultation"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          ) : (
            /* Expanded 30-70 Split Sidebar */
            <div className="flex-1 flex flex-col overflow-hidden min-h-0 w-full gap-2">
              {/* --- Upper Part: Product Classifier Diagnostic (Non-scrollable, fits naturally, shifts history dynamically) --- */}
              {showClassifier ? (
                <div className="shrink-0 flex flex-col pb-1">
                  <div className="flex items-center justify-between px-1 pb-1 shrink-0">
                    <span className="text-[11px] font-bold text-[#047857] flex items-center gap-1 uppercase tracking-tight">
                      <Sparkles className="w-3 h-3 text-[#059669]" />
                      Classifier
                    </span>
                    <button
                      type="button"
                      onClick={() => setShowClassifier(false)}
                      className="text-[10px] text-[#5C6B62] hover:text-[#047857] font-medium px-1.5 py-0.5 rounded hover:bg-white/80 transition-colors"
                      title="Hide Classifier"
                    >
                      Hide
                    </button>
                  </div>
                  <div className="w-full">
                    <ProductClassificationPanel
                      activeClassification={activeClassification}
                      productContext={productContext}
                      classificationState={classificationState}
                      onStartDiagnostic={handleStartDiagnostic}
                      onResetClassification={handleResetClassification}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between px-1 py-1 shrink-0 bg-white/50 rounded-lg border border-slate-200/50">
                  <span className="text-[11px] font-semibold text-[#5C6B62] flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-[#059669]" />
                    Classifier
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowClassifier(true)}
                    className="text-[10px] text-[#047857] hover:underline font-semibold px-1.5 py-0.5 rounded hover:bg-white/80"
                  >
                    Show
                  </button>
                </div>
              )}

              {/* Subtle Divider */}
              {showClassifier && <div className="border-t border-slate-200/60 my-0.5 shrink-0" />}

              {/* --- Lower Part (~70% height): Conversation History --- */}
              <div className="flex-1 flex flex-col min-h-0 overflow-hidden pt-0.5">
                <div className="flex items-center justify-between px-1 pb-1.5 shrink-0">
                  <span
                    className="text-[12px] font-semibold tracking-tight uppercase"
                    style={{ color: "var(--text-secondary, #5C6B62)" }}
                  >
                    History
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={startNewConsultation}
                      className="p-1 rounded-lg hover:bg-white/80 transition-colors"
                      style={{ color: "var(--accent-600, #059669)" }}
                      title="Start New Consultation"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setIsSidebarCollapsed(true)}
                      className="p-1 rounded-lg hover:bg-white/80 transition-colors"
                      style={{ color: "var(--text-muted, #8B978F)" }}
                      title="Collapse Sidebar"
                    >
                      <PanelLeftClose className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Conversation List */}
                <div className="flex-1 overflow-y-auto space-y-1.5 pr-0.5 custom-scrollbar min-h-0">
                  {conversations.length === 0 ? (
                    <p
                      className="text-[11px] px-2 py-4 text-center italic"
                      style={{ color: "var(--text-muted, #8B978F)" }}
                    >
                      No prior sessions
                    </p>
                  ) : (
                    conversations.map((conv) => {
                      const isActive = conv.id === activeConversationId;
                      return (
                        <div
                          key={conv.id}
                          onClick={() => loadConversation(conv.id)}
                          className={`group cursor-pointer transition-all p-2 rounded-xl flex items-center justify-between gap-1.5 ${
                            isActive ? "glass-history-item-active" : "glass-history-item-inactive"
                          }`}
                          title={conv.title || conv.product_name || "Consultation"}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <MessageSquare
                              className={`w-3.5 h-3.5 shrink-0 ${
                                isActive ? "text-[#047857]" : "text-[#8B978F]"
                              }`}
                            />
                            <span className="text-xs truncate font-medium">
                              {conv.product_name || conv.title || "Session"}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                            className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-rose-600 transition-opacity"
                            title="Delete"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* =========================================================================
            2. Main Chat Panel (Glass Card)
            ========================================================================= */}
        <main
          className="flex-1 flex flex-col justify-between p-3 sm:p-4 glass-panel-card relative overflow-hidden h-full min-h-0"
          style={{
            background: "var(--glass-medium, rgba(255, 255, 255, 0.65))",
            backdropFilter: "blur(var(--blur-card, 16px))",
            WebkitBackdropFilter: "blur(var(--blur-card, 16px))",
            border: "0.5px solid var(--glass-border, rgba(255, 255, 255, 0.85))",
            borderRadius: "var(--radius-card, 16px)",
            boxShadow: "var(--shadow-card, 0 12px 32px rgba(16, 60, 40, 0.10))",
          }}
        >
          {/* Top Bar inside the Panel */}
          <header className="flex items-center justify-between gap-3 pb-3 border-b border-white/60">
            {/* Left: App Title & Diagnostic Status */}
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center text-white shadow-sm"
                style={{ background: "var(--accent-gradient)" }}
              >
                <Scale className="w-3.5 h-3.5" />
              </div>
              <div>
                <h2
                  className="text-sm font-medium tracking-tight"
                  style={{ color: "var(--text-primary, #152018)" }}
                >
                  IP-SAKTI Sahayak
                </h2>
                {classificationState === "CLASSIFIED" && (activeClassification || productContext?.category) && (
                  <span className="text-[10px] font-semibold text-[#047857] flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" />
                    {activeClassification?.category_name || productContext?.category}
                  </span>
                )}
              </div>
            </div>

            {/* Right: Jurisdiction Toggle Pill & Language Selector */}
            <div className="flex items-center gap-2">
              {/* Language Selector */}
              <LanguageSelector />

              {/* Jurisdiction Toggle Pill */}
              <div
                role="group"
                aria-label="Jurisdiction Selector"
                className="flex items-center p-0.5 rounded-full border shadow-2xs"
                style={{
                  background: "rgba(241, 247, 243, 0.8)",
                  borderRadius: "var(--radius-pill, 20px)",
                  borderColor: "rgba(220, 240, 224, 0.8)",
                }}
              >
                <button
                  type="button"
                  onClick={() => setPrimary("INDIA")}
                  className={`text-xs px-3 py-1 rounded-full font-medium transition-all ${
                    primary === "INDIA"
                      ? "text-white font-semibold shadow-xs"
                      : "text-[#5C6B62] hover:text-[#152018]"
                  }`}
                  style={
                    primary === "INDIA"
                      ? {
                          background: "var(--accent-gradient)",
                          boxShadow: "0 3px 8px rgba(5,150,105,0.35)",
                        }
                      : {}
                  }
                >
                  India
                </button>
                <button
                  type="button"
                  onClick={() => setPrimary("INTERNATIONAL")}
                  className={`text-xs px-3 py-1 rounded-full font-medium transition-all ${
                    primary === "INTERNATIONAL"
                      ? "text-white font-semibold shadow-xs"
                      : "text-[#5C6B62] hover:text-[#152018]"
                  }`}
                  style={
                    primary === "INTERNATIONAL"
                      ? {
                          background: "var(--accent-gradient)",
                          boxShadow: "0 3px 8px rgba(5,150,105,0.35)",
                        }
                      : {}
                  }
                >
                  International
                </button>
              </div>
            </div>
          </header>

          {/* Messages Feed */}
          <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-1">
            {messages.map((msg: ChatMessage) => (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {/* Assistant Avatar Indicator */}
                {msg.role === "assistant" && (
                  <div
                    className="w-[26px] h-[26px] rounded-full flex items-center justify-center text-white shrink-0 shadow-xs mt-1"
                    style={{ background: "var(--accent-gradient)" }}
                  >
                    <Scale className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`space-y-1.5 max-w-[80%] ${
                    msg.role === "user" ? "items-end" : "items-start"
                  }`}
                >
                  {/* Message Bubble */}
                  <div
                    className={`p-3.5 ${
                      msg.role === "user"
                        ? "glass-user-bubble ml-auto"
                        : "glass-assistant-bubble"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <div className="space-y-2 text-[#152018]">
                        <ReactMarkdown
                          components={{
                            h1: ({ node, ...props }) => (
                              <h1 className="text-sm font-bold text-[#047857] mt-2 mb-1" {...props} />
                            ),
                            h2: ({ node, ...props }) => (
                              <h2 className="text-sm font-bold text-[#047857] mt-2 mb-1" {...props} />
                            ),
                            h3: ({ node, ...props }) => (
                              <h3 className="text-xs font-bold text-[#059669] mt-1.5 mb-1" {...props} />
                            ),
                            h4: ({ node, ...props }) => (
                              <h4 className="text-xs font-semibold text-[#152018] mt-1 mb-0.5" {...props} />
                            ),
                            p: ({ node, ...props }) => (
                              <p className="mb-1.5 leading-relaxed text-[13px] last:mb-0" {...props} />
                            ),
                            strong: ({ node, ...props }) => (
                              <strong className="font-semibold text-[#152018]" {...props} />
                            ),
                            ul: ({ node, ...props }) => (
                              <ul className="list-disc pl-4 mb-2 space-y-1 text-xs text-[#152018]" {...props} />
                            ),
                            ol: ({ node, ...props }) => (
                              <ol className="list-decimal pl-4 mb-2 space-y-1 text-xs text-[#152018]" {...props} />
                            ),
                            li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                            hr: ({ node, ...props }) => (
                              <hr className="my-2 border-slate-200" {...props} />
                            ),
                            blockquote: ({ node, ...props }) => (
                              <blockquote
                                className="pl-3 border-l-2 border-[#10B981] italic text-[#5C6B62] my-2 text-xs"
                                {...props}
                              />
                            ),
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    )}

                    {/* Classified Product Callout */}
                    {msg.product_classification && (
                      <div className="mt-2.5 p-2 rounded-lg bg-[#ECFDF5] border border-[#10B981]/30 text-xs text-[#047857] flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-[#059669] shrink-0" />
                        <div>
                          <span className="font-bold">Statutory Categorization: </span>
                          <span>
                            {msg.product_classification.category_name} (
                            {msg.product_classification.regulatory_pathway})
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Out of Scope Guardrail */}
                    {msg.out_of_scope_detected && msg.jurisdiction && (
                      <JurisdictionOutGuardrail
                        detectedJurisdiction={msg.jurisdiction}
                        query={messages[messages.indexOf(msg) - 1]?.content || ""}
                        onSwitchAndRetry={() => {
                          const lastUser = messages[messages.indexOf(msg) - 1]?.content;
                          if (lastUser) handleSendMessage(lastUser);
                        }}
                      />
                    )}
                  </div>

                  {/* Assistant Citation & Confidence Chip Row */}
                  {msg.role === "assistant" && !msg.out_of_scope_detected && !isWelcomeMessage(msg.content) && (
                    <div className="flex items-center gap-1.5 flex-wrap pt-0.5 pl-1">
                      {/* Confidence Chip */}
                      {msg.citations && msg.citations.length > 0 && (
                        <ConfidenceBadge
                          score={msg.confidence_score}
                          label={msg.confidence_label}
                          requiresReview={msg.requires_human_review}
                        />
                      )}

                      {/* Verified Statutory Citations (Fully Expanded by default, no hidden text) */}
                      {msg.citations &&
                        msg.citations.map((c, idx) => (
                          <span
                            key={c.id || idx}
                            style={{
                              backgroundColor: "var(--chip-citation-bg, #ECFDF5)",
                              color: "var(--chip-citation-text, #047857)",
                              fontSize: "10px",
                              padding: "4px 9px",
                              borderRadius: "6px",
                              border: "1px solid rgba(16, 185, 129, 0.25)",
                            }}
                            className="inline-flex items-start gap-1.5 font-medium shadow-2xs break-words max-w-full text-left leading-snug"
                            title={`${c.document_title} - ${c.section_ref} (${c.jurisdiction || "Statutory Authority"})`}
                          >
                            <BookOpen className="w-3 h-3 shrink-0 text-emerald-600 mt-0.5" />
                            <span className="break-words">
                              <span className="font-bold">{c.document_title?.replace(".pdf", "")}</span>
                              <span className="text-[#059669] font-mono font-medium"> — {c.section_ref}</span>
                              {c.jurisdiction && (
                                <span className="ml-1 text-[9px] uppercase px-1 py-0.2 rounded bg-emerald-100/60 font-semibold">
                                  {c.jurisdiction}
                                </span>
                              )}
                            </span>
                          </span>
                        ))}

                      {/* Escalation Prompt Chip / Action - Always accessible to consult accredited IP Facilitator */}
                      {!msg.id?.startsWith("err-") && (
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedMessageId(msg.id);
                            setEscalateModalOpen(true);
                          }}
                          style={{
                            backgroundColor: "#FEF3C7",
                            color: "#92400E",
                            fontSize: "11px",
                            padding: "4px 10px",
                            borderRadius: "7px",
                            border: "1px solid #FCD34D",
                          }}
                          className="inline-flex items-center gap-1.5 font-semibold hover:bg-amber-200 transition-colors shadow-xs cursor-pointer"
                          title="Escalate to Human IP Facilitator"
                        >
                          <HelpCircle className="w-3 h-3" />
                          <span>Ask IP Facilitator / Human Expert</span>
                        </button>
                      )}

                      {/* Translation Badge */}
                      {msg.is_translated && (
                        <span className="text-[10px] text-[#059669] flex items-center gap-0.5 font-medium ml-1">
                          <Languages className="w-2.5 h-2.5" />
                          Sarvam AI
                        </span>
                      )}

                      {/* Thumbs Feedback */}
                      <div className="flex items-center gap-1 ml-auto">
                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.id, 5)}
                          aria-label="Helpful"
                          className={`p-0.5 rounded hover:bg-white/80 ${
                            feedbackMap[msg.id] === 5 ? "text-[#059669] font-bold" : "text-[#8B978F]"
                          }`}
                        >
                          <ThumbsUp className="w-3 h-3" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFeedback(msg.id, 1)}
                          aria-label="Unhelpful"
                          className={`p-0.5 rounded hover:bg-white/80 ${
                            feedbackMap[msg.id] === 1 ? "text-rose-600 font-bold" : "text-[#8B978F]"
                          }`}
                        >
                          <ThumbsDown className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Sample Starters (Initial conversation only) */}
            {messages.length === 1 && (
              <div className="pt-2">
                <span
                  className="text-[11px] font-medium block mb-1.5"
                  style={{ color: "var(--text-secondary, #5C6B62)" }}
                >
                  {getSampleQueriesHeading(selectedLanguage)}
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {getSampleQueries(selectedLanguage).map((sq, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendMessage(sq)}
                      className="p-2.5 text-left text-xs rounded-xl glass-history-item-inactive hover:bg-white transition-all text-[#152018]"
                    >
                      "{sq}"
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Loading Indicator */}
            {isSending && (
              <div className="flex gap-2.5 justify-start items-center">
                <div
                  className="w-[26px] h-[26px] rounded-full flex items-center justify-center text-white shrink-0 shadow-xs"
                  style={{ background: "var(--accent-gradient)" }}
                >
                  <Scale className="w-3.5 h-3.5" />
                </div>
                <div className="p-3 rounded-2xl glass-assistant-bubble text-xs flex items-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-[#059669]" />
                  <span className="font-medium text-[#5C6B62]">
                    Analyzing statutory grounding and evaluating compliance...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* =========================================================================
              3. Input Bar & Voice Controls (Pill Container)
              ========================================================================= */}
          <div className="space-y-2 pt-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(input);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 glass-input-bar"
            >
              {/* Text Input */}
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  classificationState === "CLASSIFIED"
                    ? "Ask about patentability (§3(p)), ABS, or licensing for your classified product..."
                    : "Describe your product formulation, herbal ingredients, or IPR query..."
                }
                disabled={isSending}
                style={{
                  color: "var(--text-primary, #152018)",
                }}
                className="flex-1 bg-transparent border-0 text-sm placeholder:text-[#8B978F] focus:outline-none focus:ring-0 px-2"
              />

              {/* Dictation Mic Button */}
              <VoiceInputButton
                onTranscript={(transcript) => setInput(transcript)}
                disabled={isSending}
              />

              {/* Full Hands-Free Voice Mode Button (4 States) */}
              <VoiceConversationButton
                jurisdiction={active}
                intent={initialIntent || undefined}
                disabled={isSending}
              />

              {/* Send Button */}
              <button
                type="submit"
                disabled={!input.trim() || isSending}
                style={{
                  background: "var(--accent-gradient, linear-gradient(135deg, #10B981, #059669))",
                  boxShadow: "0 4px 12px rgba(5, 150, 105, 0.4)",
                }}
                className="w-9 h-9 rounded-full flex items-center justify-center text-white shrink-0 hover:scale-105 active:scale-95 transition-transform disabled:opacity-50 disabled:scale-100"
                title="Send query"
              >
                {isSending ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white" />
                ) : (
                  <Send className="w-3.5 h-3.5 text-white" />
                )}
              </button>
            </form>

            {/* 4. Disclaimer Footer */}
            <p
              className="text-[10px] text-center tracking-tight"
              style={{ color: "var(--text-muted, #8B978F)" }}
            >
              Statutory Notice: IP-SAKTI Sahayak provides verified legal/regulatory information, not legal advice. Official filings require review by a registered patent agent or legal counsel.
            </p>
          </div>
        </main>
      </div>

      {/* Human Facilitator Escalation Modal with Autofilled Context */}
      {(() => {
        const targetAssistantMsg = selectedMessageId
          ? messages.find((m) => m.id === selectedMessageId)
          : messages.filter((m) => m.role === "assistant").slice(-1)[0];
        const targetAssistantIdx = targetAssistantMsg ? messages.indexOf(targetAssistantMsg) : -1;
        const targetUserMsg =
          targetAssistantIdx > 0
            ? messages[targetAssistantIdx - 1]
            : messages.filter((m) => m.role === "user").slice(-1)[0];

        return (
          <ExpertEscalationModal
            isOpen={escalateModalOpen}
            onClose={() => setEscalateModalOpen(false)}
            messageId={targetAssistantMsg?.id}
            userQuery={targetUserMsg?.content}
            assistantResponse={targetAssistantMsg?.content}
            confidenceScore={targetAssistantMsg?.confidence_score}
            confidenceLabel={targetAssistantMsg?.confidence_label}
            productContext={productContext}
            activeClassification={activeClassification}
          />
        );
      })()}
    </div>
  );
};
