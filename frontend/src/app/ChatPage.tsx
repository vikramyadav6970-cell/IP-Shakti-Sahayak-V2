import React, { useState, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  Sparkles,
  Send,
  Loader2,
  Scale,
  HelpCircle,
  Layers,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  Package,
  Plus,
  Languages,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useJurisdiction } from "@/store/useJurisdictionStore";
import { useChatStore } from "@/store/useChatStore";
import { chatService } from "@/services/chatService";
import { CitationCard } from "@/components/chat/CitationCard";
import { ConfidenceBadge } from "@/components/chat/ConfidenceBadge";
import { JurisdictionOutGuardrail } from "@/components/chat/JurisdictionOutGuardrail";
import { ExpertEscalationModal } from "@/components/chat/ExpertEscalationModal";
import { ProductClassificationPanel } from "@/components/chat/ProductClassificationPanel";
import { ProductHistorySidebar } from "@/components/chat/ProductHistorySidebar";
import { LanguageSelector } from "@/components/chat/LanguageSelector";
import { VoiceInputButton } from "@/components/chat/VoiceInputButton";
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
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [feedbackMap, setFeedbackMap] = useState<Record<string, number>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { primary, active } = useJurisdiction();

  // Zustand Store
  const {
    messages,
    productContext,
    activeClassification,
    classificationState,
    conversations,
    isSending,
    selectedLanguage,
    sendMessage,
    startNewConsultation,
    toggleHistory,
    fetchConversations,
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

  // If initial query provided via URL param, execute automatically if messages empty/new
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

  return (
    <div className="max-w-7xl mx-auto space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-600" />
            IP & Regulatory AI Consultation
          </h1>
          <p className="text-xs text-slate-500">
            Active Jurisdiction: <strong className="text-emerald-700 dark:text-emerald-400">{active}</strong>
            {classificationState === "CLASSIFIED" && (activeClassification || productContext?.category) && (
              <span className="ml-2 inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-semibold">
                <CheckCircle2 className="w-3 h-3" />
                Classified: {activeClassification?.category_name || productContext?.category}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Language Selector (Powered by Sarvam AI) */}
          <LanguageSelector />

          {/* Product History Drawer Trigger */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => toggleHistory(true)}
            className="text-xs gap-1.5 h-8 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 font-semibold"
          >
            <Package className="w-3.5 h-3.5 text-emerald-600" />
            <span>Product History ({conversations.length})</span>
          </Button>

          {/* New Product Consultation */}
          <Button
            variant="outline"
            size="sm"
            onClick={startNewConsultation}
            className="text-xs gap-1.5 h-8 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/50 font-semibold"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Product</span>
          </Button>

          {/* Toggle Classifier Panel */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="text-xs gap-1.5 h-8 text-slate-500 hover:text-slate-900 dark:hover:text-slate-100"
          >
            <Layers className="w-3.5 h-3.5 text-emerald-600" />
            <span>{isSidebarOpen ? "Hide Classifier" : "Show Classifier"}</span>
          </Button>
        </div>
      </div>

      {/* Main 2-Column Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start">
        {/* Left Column: Product Classifier Card & 6 Categories */}
        {isSidebarOpen && (
          <aside className="lg:col-span-4 h-[640px] overflow-hidden">
            <ProductClassificationPanel
              activeClassification={activeClassification}
              productContext={productContext}
              classificationState={classificationState}
              onStartDiagnostic={handleStartDiagnostic}
              onResetClassification={handleResetClassification}
            />
          </aside>
        )}

        {/* Right Column: Chat Consultation Interface */}
        <section className={`${isSidebarOpen ? "lg:col-span-8" : "lg:col-span-12"} transition-all`}>
          <Card className="h-[640px] flex flex-col justify-between p-4 bg-white/70 dark:bg-slate-900/70 backdrop-blur shadow-sm">
            {/* Messages List */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-lg bg-emerald-700 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                      <Scale className="w-4 h-4" />
                    </div>
                  )}

                  <div className={`space-y-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                    {/* Message Bubble */}
                    <div
                      className={`p-3.5 rounded-2xl text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-emerald-700 text-white rounded-br-sm"
                          : "bg-slate-100 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 rounded-bl-sm border border-slate-200/80 dark:border-slate-700/60"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      ) : (
                        <div className="space-y-2 text-slate-800 dark:text-slate-100">
                          <ReactMarkdown
                            components={{
                              h1: ({ node, ...props }) => <h1 className="text-base font-bold text-emerald-800 dark:text-emerald-300 mt-2 mb-1" {...props} />,
                              h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-emerald-800 dark:text-emerald-300 mt-2 mb-1" {...props} />,
                              h3: ({ node, ...props }) => <h3 className="text-sm font-bold text-emerald-700 dark:text-emerald-400 mt-2 mb-1" {...props} />,
                              h4: ({ node, ...props }) => <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-200 mt-1.5 mb-0.5" {...props} />,
                              p: ({ node, ...props }) => <p className="mb-2 leading-relaxed text-sm last:mb-0" {...props} />,
                              strong: ({ node, ...props }) => <strong className="font-semibold text-slate-900 dark:text-slate-50" {...props} />,
                              ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-sm text-slate-700 dark:text-slate-200" {...props} />,
                              ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-sm text-slate-700 dark:text-slate-200" {...props} />,
                              li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                              hr: ({ node, ...props }) => <hr className="my-2.5 border-slate-300 dark:border-slate-700" {...props} />,
                              blockquote: ({ node, ...props }) => (
                                <blockquote className="pl-3 border-l-2 border-emerald-500 italic text-slate-600 dark:text-slate-400 my-2" {...props} />
                              ),
                            }}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      )}

                      {/* If this turn classified a product, render a highlight badge inside the message */}
                      {msg.product_classification && (
                        <div className="mt-3 p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-700/60 text-xs text-emerald-900 dark:text-emerald-200 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                          <div>
                            <span className="font-bold text-emerald-950 dark:text-emerald-100">Statutory Categorization: </span>
                            <span>{msg.product_classification.category_name} ({msg.product_classification.regulatory_pathway})</span>
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

                    {/* Assistant Citations & Grounding Header — ONLY when based on RAG citations */}
                    {msg.role === "assistant" && !msg.out_of_scope_detected && !isWelcomeMessage(msg.content) && (
                      <div className="space-y-2 pt-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          {/* Grounding Confidence Badge ONLY when RAG data retrieval citations exist */}
                          {msg.citations && msg.citations.length > 0 && (
                            <ConfidenceBadge
                              score={msg.confidence_score}
                              label={msg.confidence_label}
                              requiresReview={msg.requires_human_review}
                            />
                          )}

                          {/* Sarvam AI Translation Badge */}
                          {msg.is_translated && (
                            <Badge variant="outline" className="text-[10px] gap-1 px-2 py-0.5 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/40 font-medium">
                              <Languages className="w-2.5 h-2.5" />
                              Sarvam AI Translated
                            </Badge>
                          )}

                          {/* Thumbs up / down feedback */}
                          <div className="flex items-center gap-1 ml-auto">
                            <button
                              type="button"
                              onClick={() => {
                                setSelectedMessageId(msg.id);
                                setEscalateModalOpen(true);
                              }}
                              className="inline-flex items-center gap-1 text-[11px] text-slate-400 hover:text-emerald-700 dark:hover:text-emerald-300 mr-2"
                              title="Escalate to Human IP Facilitator"
                            >
                              <HelpCircle className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Ask Human Expert</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => handleFeedback(msg.id, 5)}
                              aria-label="Helpful"
                              className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 ${
                                feedbackMap[msg.id] === 5 ? "text-emerald-600 font-bold" : "text-slate-400"
                              }`}
                            >
                              <ThumbsUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleFeedback(msg.id, 1)}
                              aria-label="Unhelpful"
                              className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 ${
                                feedbackMap[msg.id] === 1 ? "text-rose-600 font-bold" : "text-slate-400"
                              }`}
                            >
                              <ThumbsDown className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>

                        {/* Citations Grid ONLY when RAG data retrieval citations exist */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="space-y-1.5 pt-1">
                            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block">
                              Statutory Citations ({msg.citations.length})
                            </span>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {msg.citations.map((c, idx) => (
                                <CitationCard key={c.id || idx} citation={c} />
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Sample Starters Hint (Only visible right at the beginning) */}
              {messages.length === 1 && (
                <div className="pt-2">
                  <span className="text-[11px] text-slate-500 font-medium block mb-1.5">
                    {getSampleQueriesHeading(selectedLanguage)}
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {getSampleQueries(selectedLanguage).map((sq, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleSendMessage(sq)}
                        className="p-2.5 text-left text-xs rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/40 hover:bg-emerald-50 dark:hover:bg-emerald-950/30 hover:border-emerald-500/40 transition-colors text-slate-700 dark:text-slate-300"
                      >
                        "{sq}"
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Multilingual Loading Indicator */}
              {isSending && (
                <div className="flex gap-3 justify-start items-center">
                  <div className="w-8 h-8 rounded-lg bg-emerald-700 text-white flex items-center justify-center shrink-0">
                    <Scale className="w-4 h-4" />
                  </div>
                  <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-slate-800 text-xs flex flex-col gap-1 text-slate-500">
                    <div className="flex items-center gap-2">
                      <Loader2 className="w-4 h-4 animate-spin text-emerald-600" />
                      <span className="font-medium text-slate-700 dark:text-slate-200">
                        {selectedLanguage !== "en-IN" && selectedLanguage !== "en"
                          ? "Processing multilingual formulation query..."
                          : "Analyzing formulation & evaluating patentability..."}
                      </span>
                    </div>
                    {selectedLanguage !== "en-IN" && selectedLanguage !== "en" && (
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 pl-6">
                        <Languages className="w-3 h-3" />
                        Sarvam AI Translation & Statutory RAG pipeline active
                      </span>
                    )}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Bar */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(input);
              }}
              className="flex items-center gap-2 pt-3 border-t border-slate-200 dark:border-slate-800"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  classificationState === "CLASSIFIED"
                    ? `Ask about patentability (§3(p)), ABS, or licensing for your classified product...`
                    : classificationState === "COLLECTING_PRODUCT_INFORMATION"
                    ? "Provide additional formulation or ingredient details..."
                    : "Describe your product name, ingredients, and formulation method..."
                }
                disabled={isSending}
                className="flex-1 h-11 px-3.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-600 dark:text-white"
              />

              {/* Voice Speech-to-Text Input Button */}
              <VoiceInputButton
                onTranscript={(transcript) => setInput(transcript)}
                disabled={isSending}
              />

              <Button
                type="submit"
                disabled={!input.trim() || isSending}
                className="h-11 px-4 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm shrink-0"
              >
                {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </Button>
            </form>
          </Card>
        </section>
      </div>

      {/* Slide-over Product Formulation History Sidebar */}
      <ProductHistorySidebar />

      {/* Human Facilitator Escalation Modal */}
      <ExpertEscalationModal
        isOpen={escalateModalOpen}
        onClose={() => setEscalateModalOpen(false)}
        messageId={selectedMessageId}
      />
    </div>
  );
};
