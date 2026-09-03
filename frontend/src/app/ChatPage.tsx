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
  Layers,
  Sparkles,
  ChevronDown,
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
  const [showClassifierDrawer, setShowClassifierDrawer] = useState(false);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, number>>({});
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

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

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    setIsScrolledUp(scrollHeight - scrollTop - clientHeight > 100);
  };

  useEffect(() => {
    if (!isScrolledUp) {
      scrollToBottom();
    }
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
    <div className="h-full w-full overflow-hidden flex flex-col min-h-0 bg-transparent">
      {/* Workspace: Collapsible Sidebar + Main Chat Panel */}
      <div className="flex flex-col lg:flex-row gap-3 items-start max-w-[1600px] w-full mx-auto h-full overflow-hidden min-h-0">
        {/* =========================================================================
            1. Left Sidebar: Product Classifier (TOP) + History (BELOW)
            ========================================================================= */}
        <aside
          aria-label="Product Diagnostic & History"
          className={`shrink-0 flex flex-col justify-start transition-all duration-300 ease-in-out rounded-2xl p-2.5 border border-slate-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 shadow-xl ${
            isSidebarCollapsed
              ? "w-14 h-fit"
              : showClassifierDrawer
                ? "w-full lg:w-80 h-full overflow-hidden"
                : conversations.length === 0
                  ? "w-full lg:w-56 h-fit"
                  : "w-full lg:w-56 h-fit max-h-full overflow-hidden"
          }`}
        >
          <div className="space-y-3 w-full flex flex-col overflow-hidden">
            {/* 1. TOP BLOCK: Product Classifier (BEFORE / ON TOP OF History) */}
            <div className="w-full">
              {!isSidebarCollapsed ? (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between px-1">
                    <span className="text-[10px] font-bold tracking-wider uppercase text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      <span>Diagnostics</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => setIsSidebarCollapsed(true)}
                      className="p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors cursor-pointer"
                      title="Collapse Sidebar"
                    >
                      <PanelLeftClose className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <button
                    type="button"
                    onClick={() => setShowClassifierDrawer(!showClassifierDrawer)}
                    className={`group relative overflow-hidden w-full flex items-center justify-between gap-1.5 py-2 px-2.5 rounded-xl text-xs font-semibold border transition-all duration-500 cursor-pointer shadow-xs ${
                      showClassifierDrawer
                        ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-emerald-500 shadow-emerald-950/40"
                        : "bg-emerald-50 dark:bg-slate-950/80 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-slate-800 hover:border-emerald-500/60 hover:shadow-md hover:shadow-emerald-950/30"
                    }`}
                    title="Toggle Product Diagnostic Panel"
                  >
                    {/* Landing Page signature radial expanding fluid fill from center */}
                    <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400/90 via-emerald-500/90 to-teal-600/90 group-hover:w-[450px] group-hover:h-[450px] transition-all duration-700 ease-out pointer-events-none" />

                    <div className="relative z-10 flex items-center gap-1.5">
                      <Layers className={`w-3.5 h-3.5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-6 ${
                        showClassifierDrawer ? "text-white" : "text-emerald-600 dark:text-emerald-400 group-hover:text-white"
                      }`} />
                      <span className={`font-bold transition-colors ${
                        showClassifierDrawer ? "text-white" : "group-hover:text-white"
                      }`}>
                        Product Classifier
                      </span>
                    </div>

                    <span className={`relative z-10 text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider transition-all duration-300 ${
                      showClassifierDrawer
                        ? "bg-white/20 text-white"
                        : "bg-emerald-200/60 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-400 border border-emerald-300/60 dark:border-emerald-800 group-hover:bg-white/25 group-hover:text-white group-hover:border-transparent"
                    }`}>
                      {showClassifierDrawer ? "Active" : "Open"}
                    </span>
                  </button>

                  {/* If Classifier is active, render the diagnostic panel right here */}
                  {showClassifierDrawer && (
                    <div className="overflow-y-auto pr-0.5 custom-scrollbar border-t border-slate-200 dark:border-slate-800 pt-2 max-h-[50vh]">
                      <ProductClassificationPanel
                        activeClassification={activeClassification}
                        productContext={productContext}
                        classificationState={classificationState}
                        onStartDiagnostic={handleStartDiagnostic}
                        onResetClassification={handleResetClassification}
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-full flex flex-col items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsSidebarCollapsed(false)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-emerald-600 dark:text-emerald-400 transition-colors cursor-pointer"
                    title="Expand History Sidebar"
                  >
                    <PanelLeftOpen className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsSidebarCollapsed(false);
                      setShowClassifierDrawer(true);
                    }}
                    className="p-1.5 rounded-lg bg-emerald-50 dark:bg-slate-800 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-slate-700 transition-colors cursor-pointer"
                    title="Product Classifier"
                  >
                    <Layers className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>

            {/* Subtle Divider between Classifier and History */}
            {!isSidebarCollapsed && <div className="border-t border-slate-200 dark:border-slate-800" />}

            {/* 2. BELOW BLOCK: Consultation History */}
            <div className="space-y-2 w-full flex flex-col overflow-hidden">
              <div className="flex items-center justify-between px-1">
                {!isSidebarCollapsed ? (
                  <>
                    <span className="text-[10px] font-bold tracking-wider uppercase text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <MessageSquare className="w-3 h-3 text-slate-400" />
                      <span>History</span>
                    </span>
                    <button
                      type="button"
                      onClick={startNewConsultation}
                      className="group relative overflow-hidden p-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 hover:border-emerald-400/60 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 transition-all duration-300 cursor-pointer flex items-center gap-1 text-[10px] font-semibold px-2 shadow-2xs"
                      title="Start New Consultation"
                    >
                      <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400 via-emerald-500 to-teal-600 group-hover:w-[150px] group-hover:h-[150px] transition-all duration-500 ease-out pointer-events-none" />
                      <Plus className="w-3 h-3 relative z-10 group-hover:text-white transition-colors" />
                      <span className="relative z-10 group-hover:text-white transition-colors">New</span>
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={startNewConsultation}
                    className="p-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 hover:bg-emerald-100 dark:hover:bg-emerald-900/80 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 transition-colors cursor-pointer"
                    title="New Consultation"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* History List */}
              {!isSidebarCollapsed && (
                <div className="overflow-y-auto space-y-1.5 pr-0.5 custom-scrollbar max-h-[35vh]">
                  {conversations.length === 0 ? (
                    <div className="px-2 py-3 text-center rounded-xl bg-slate-100/60 dark:bg-slate-950/40 border border-slate-200 dark:border-slate-800/60">
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 italic">
                        No prior sessions
                      </p>
                    </div>
                  ) : (
                    conversations.map((conv) => {
                      const isActive = conv.id === activeConversationId;
                      return (
                        <div
                          key={conv.id}
                          onClick={() => loadConversation(conv.id)}
                          className={`group cursor-pointer transition-all p-2 rounded-xl flex items-center justify-between gap-1.5 ${
                            isActive
                              ? "bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-500/50 text-emerald-900 dark:text-white shadow-xs font-semibold"
                              : "bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800/80 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-white"
                          }`}
                          title={conv.title || conv.product_name || "Consultation"}
                        >
                          <div className="flex items-center gap-2 truncate">
                            <MessageSquare
                              className={`w-3.5 h-3.5 shrink-0 ${
                                isActive ? "text-emerald-600 dark:text-emerald-400" : "text-slate-400"
                              }`}
                            />
                            <span className="text-xs truncate">
                              {conv.product_name || conv.title || "Session"}
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => handleDeleteConversation(e, conv.id)}
                            className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-rose-500 transition-opacity cursor-pointer"
                            title="Delete"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* =========================================================================
            2. Main Chat Panel (Fixed Height, ChatGPT/Gemini Stream Scroll)
            ========================================================================= */}
        <main className="flex-1 h-full flex flex-col justify-between p-3 sm:p-4 rounded-2xl relative overflow-hidden min-h-0 bg-white/90 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-xl backdrop-blur-xl">
          {/* Top Bar inside the Panel */}
          <header className="flex items-center justify-between gap-3 pb-2.5 border-b border-slate-200 dark:border-slate-800 shrink-0">
            {/* Left: App Title & Diagnostic Status */}
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-700 flex items-center justify-center text-white shadow-sm border border-emerald-400/30">
                <Scale className="w-3.5 h-3.5" />
              </div>
              <div>
                <h2 className="text-sm font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span>IP-SAKTI Sahayak</span>
                </h2>
                {classificationState === "CLASSIFIED" && (activeClassification || productContext?.category) && (
                  <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
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
                className="flex items-center p-0.5 rounded-full border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 shadow-2xs"
              >
                <button
                  type="button"
                  onClick={() => setPrimary("INDIA")}
                  className={`text-xs px-3 py-1 rounded-full font-medium transition-all cursor-pointer ${
                    primary === "INDIA"
                      ? "text-white font-bold bg-gradient-to-r from-emerald-600 to-teal-600 shadow-xs"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  India
                </button>
                <button
                  type="button"
                  onClick={() => setPrimary("INTERNATIONAL")}
                  className={`text-xs px-3 py-1 rounded-full font-medium transition-all cursor-pointer ${
                    primary === "INTERNATIONAL"
                      ? "text-white font-bold bg-gradient-to-r from-emerald-600 to-teal-600 shadow-xs"
                      : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  }`}
                >
                  International
                </button>
              </div>
            </div>
          </header>

          {/* Messages Feed (Scrollable with Emerald Custom Scrollbar & Green Arrows) */}
          <div
            ref={messagesContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto space-y-4 py-3 pr-1 min-h-0 custom-scrollbar relative"
          >
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
                        : "rounded-2xl bg-slate-100/95 dark:bg-slate-950/90 border border-slate-200 dark:border-slate-800 shadow-md text-slate-900 dark:text-white"
                    }`}
                  >
                    {msg.role === "user" ? (
                      <p className="whitespace-pre-wrap text-white">{msg.content}</p>
                    ) : (
                      <div className="space-y-2 text-slate-800 dark:text-white">
                        <ReactMarkdown
                          components={{
                            h1: ({ node, ...props }) => (
                              <h1 className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-2 mb-1" {...props} />
                            ),
                            h2: ({ node, ...props }) => (
                              <h2 className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mt-2 mb-1" {...props} />
                            ),
                            h3: ({ node, ...props }) => (
                              <h3 className="text-xs font-bold text-emerald-700 dark:text-emerald-300 mt-1.5 mb-1" {...props} />
                            ),
                            h4: ({ node, ...props }) => (
                              <h4 className="text-xs font-semibold text-slate-900 dark:text-white mt-1 mb-0.5" {...props} />
                            ),
                            p: ({ node, ...props }) => (
                              <p className="mb-1.5 leading-relaxed text-[13px] text-slate-800 dark:text-slate-100 last:mb-0" {...props} />
                            ),
                            strong: ({ node, ...props }) => (
                              <strong className="font-bold text-slate-950 dark:text-white" {...props} />
                            ),
                            ul: ({ node, ...props }) => (
                              <ul className="list-disc pl-4 mb-2 space-y-1 text-xs text-slate-700 dark:text-slate-200" {...props} />
                            ),
                            ol: ({ node, ...props }) => (
                              <ol className="list-decimal pl-4 mb-2 space-y-1 text-xs text-slate-700 dark:text-slate-200" {...props} />
                            ),
                            li: ({ node, ...props }) => <li className="leading-relaxed text-slate-700 dark:text-slate-200" {...props} />,
                            hr: ({ node, ...props }) => (
                              <hr className="my-2 border-slate-300 dark:border-slate-700" {...props} />
                            ),
                            blockquote: ({ node, ...props }) => (
                              <blockquote
                                className="pl-3 border-l-2 border-emerald-500 italic text-slate-600 dark:text-slate-300 my-2 text-xs"
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
                      <div className="mt-2.5 p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/80 border border-emerald-300 dark:border-emerald-500/40 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                        <div>
                          <span className="font-bold text-slate-900 dark:text-white">Statutory Categorization: </span>
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

                      {/* Citation Chips */}
                      {msg.citations &&
                        msg.citations.map((c, idx) => (
                          <span
                            key={c.id || idx}
                            style={{
                              backgroundColor: "var(--chip-citation-bg, #ECFDF5)",
                              color: "var(--chip-citation-text, #047857)",
                              fontSize: "10px",
                              padding: "3px 8px",
                              borderRadius: "6px",
                              border: "1px solid rgba(16, 185, 129, 0.2)",
                            }}
                            className="inline-flex items-center gap-1 font-medium shadow-2xs"
                            title={`${c.document_title} - ${c.section_ref}`}
                          >
                            <BookOpen className="w-2.5 h-2.5" />
                            <span>
                              {c.document_title?.replace(".pdf", "")?.slice(0, 24)}, {c.section_ref}
                            </span>
                          </span>
                        ))}

                      {/* Escalation Prompt Chip / Action */}
                      {(msg.requires_human_review || msg.confidence_label === "LOW") && (
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedMessageId(msg.id);
                            setEscalateModalOpen(true);
                          }}
                          style={{
                            backgroundColor: "#FEF3C7",
                            color: "#92400E",
                            fontSize: "10px",
                            padding: "3px 8px",
                            borderRadius: "6px",
                            border: "1px solid #FCD34D",
                          }}
                          className="inline-flex items-center gap-1 font-semibold hover:bg-amber-200 transition-colors shadow-2xs"
                          title="Escalate to Human IP Facilitator"
                        >
                          <HelpCircle className="w-2.5 h-2.5" />
                          <span>Ask Human Expert</span>
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
                <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400 block mb-1.5">
                  {getSampleQueriesHeading(selectedLanguage)}
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {getSampleQueries(selectedLanguage).map((sq, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => handleSendMessage(sq)}
                      className="p-2.5 text-left text-xs rounded-xl bg-slate-50 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 hover:border-emerald-500/60 hover:bg-emerald-50/50 dark:hover:bg-slate-800/90 hover:text-emerald-700 dark:hover:text-emerald-300 transition-all duration-200 text-slate-800 dark:text-white font-medium shadow-2xs cursor-pointer"
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
                <div className="p-3 rounded-2xl bg-slate-100 dark:bg-slate-950/90 border border-slate-200 dark:border-slate-800 text-xs flex items-center gap-2 text-slate-700 dark:text-slate-300">
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600 dark:text-emerald-400" />
                  <span className="font-medium">
                    Analyzing statutory grounding and evaluating compliance...
                  </span>
                </div>
              </div>
            )}

            {/* Floating Dynamic Green Scroll-to-Latest Button with Green Arrow */}
            {isScrolledUp && (
              <div className="sticky bottom-2 flex justify-center w-full pointer-events-none z-20">
                <button
                  type="button"
                  onClick={scrollToBottom}
                  className="pointer-events-auto group relative overflow-hidden flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-xs font-bold shadow-lg shadow-emerald-950/40 border border-emerald-400/50 hover:shadow-xl hover:shadow-emerald-500/30 transition-all duration-300 animate-bounce cursor-pointer"
                  title="Scroll to latest message"
                >
                  <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-300 via-emerald-400 to-teal-400 group-hover:w-[160px] group-hover:h-[160px] transition-all duration-500 ease-out pointer-events-none" />
                  <span className="relative z-10 text-[11px]">Latest messages</span>
                  <ChevronDown className="w-3.5 h-3.5 relative z-10 text-emerald-200 stroke-[3] group-hover:translate-y-0.5 transition-transform" />
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* =========================================================================
              3. Input Bar & Voice Controls (Pill Container)
              ========================================================================= */}
          <div className="space-y-1.5 pt-2 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(input);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/95 dark:bg-slate-950/90 border border-slate-200 dark:border-slate-800 shadow-xl text-slate-900 dark:text-white backdrop-blur-md"
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
                className="flex-1 bg-transparent border-0 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-0 px-2"
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

              {/* Send Button with Radial Center-Out Fill */}
              <button
                type="submit"
                disabled={!input.trim() || isSending}
                style={{
                  background: "linear-gradient(135deg, #10B981, #059669)",
                  boxShadow: "0 4px 12px rgba(5, 150, 105, 0.4)",
                }}
                className="group relative overflow-hidden w-9 h-9 rounded-full flex items-center justify-center text-white shrink-0 hover:scale-105 active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:scale-100 cursor-pointer shadow-md shadow-emerald-800/30"
                title="Send query"
              >
                <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-300 via-emerald-400 to-teal-400 group-hover:w-[90px] group-hover:h-[90px] transition-all duration-500 ease-out pointer-events-none" />
                {isSending ? (
                  <Loader2 className="w-4 h-4 animate-spin text-white relative z-10" />
                ) : (
                  <Send className="w-3.5 h-3.5 text-white relative z-10 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                )}
              </button>
            </form>

            {/* 4. Disclaimer Footer */}
            <p className="text-[10px] text-center tracking-tight text-slate-500 dark:text-slate-400">
              Statutory Notice: IP-SAKTI Sahayak provides verified legal/regulatory information, not legal advice. Official filings require review by a registered patent agent or legal counsel.
            </p>
          </div>
        </main>
      </div>

      {/* Human Facilitator Escalation Modal */}
      <ExpertEscalationModal
        isOpen={escalateModalOpen}
        onClose={() => setEscalateModalOpen(false)}
        messageId={selectedMessageId}
      />
    </div>
  );
};
