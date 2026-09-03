import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Loader2,
  X,
  FileQuestion,
  Search,
  Share2,
  Calendar,
  Sparkles,
  Bot,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { expertService, ExpertRequestItem } from "@/services/expertService";
import { ProductContextData, ProductClassificationMeta } from "@/types";
import { ConfidenceBadge } from "@/components/chat/ConfidenceBadge";

interface ExpertEscalationModalProps {
  isOpen: boolean;
  onClose: () => void;
  messageId?: string;
  userQuery?: string;
  assistantResponse?: string;
  confidenceScore?: number;
  confidenceLabel?: string;
  productContext?: ProductContextData | null;
  activeClassification?: ProductClassificationMeta | null;
}

type EscalationCategory =
  | "SUBMIT_QUESTION"
  | "REQUEST_CLARIFICATION"
  | "SHARE_SOURCES"
  | "BOOK_CONSULTATION";

const ESCALATION_OPTIONS: {
  id: EscalationCategory;
  label: string;
  desc: string;
  icon: any;
}[] = [
  {
    id: "SUBMIT_QUESTION",
    label: "Submit question to IP Facilitator",
    desc: "Route query for human legal evaluation when AI response is uncertain or requires statutory review.",
    icon: FileQuestion,
  },
  {
    id: "REQUEST_CLARIFICATION",
    label: "Request clarification on this answer",
    desc: "Ask an IP specialist to clarify specific patentability §3(p), ABS, or licensing nuances.",
    icon: Search,
  },
  {
    id: "SHARE_SOURCES",
    label: "Share sources & formulation with facilitator",
    desc: "Send retrieved statutory provisions, monographs, and formulation details for expert dossier check.",
    icon: Share2,
  },
  {
    id: "BOOK_CONSULTATION",
    label: "Book advisory consultation",
    desc: "Request a 1-on-1 advisory session with an institutional Ayurvedic IP facilitator.",
    icon: Calendar,
  },
];

export const ExpertEscalationModal: React.FC<ExpertEscalationModalProps> = ({
  isOpen,
  onClose,
  messageId,
  userQuery,
  assistantResponse,
  confidenceScore,
  confidenceLabel,
  productContext,
  activeClassification,
}) => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<EscalationCategory>("SUBMIT_QUESTION");
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [urgency, setUrgency] = useState<"NORMAL" | "HIGH" | "URGENT">("NORMAL");
  const [isLoading, setIsLoading] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<ExpertRequestItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const productName =
    productContext?.product_name || activeClassification?.product_name || "Ayurvedic Formulation";
  const productCategory =
    activeClassification?.category_name || productContext?.category_name || productContext?.category || "Under Diagnostic";
  const productDetails =
    productContext?.description ||
    productContext?.formulation ||
    (productContext?.ingredients && productContext.ingredients.length > 0
      ? `Ingredients: ${productContext.ingredients.join(", ")}`
      : "Standard formulation dossier");

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsLoading(true);

    try {
      const optionLabel = ESCALATION_OPTIONS.find((o) => o.id === selectedCategory)?.label || "";
      
      const fullContext = `[Category: ${optionLabel}]
[Product: ${productName} (${productCategory})]
[Formulation Details: ${productDetails}]
[User Question: ${userQuery || "N/A"}]
[AI Generated Answer: ${assistantResponse ? assistantResponse.slice(0, 300) + "..." : "N/A"}]
[Confidence: ${confidenceLabel || "LOW"}]
[Additional User Notes: ${additionalNotes.trim() || "None provided"}]`;

      const ticket = await expertService.escalate({
        message_id: messageId,
        issue_description: fullContext,
        urgency_level: urgency,
      });
      setCreatedTicket(ticket);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit escalation request.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedCategory("SUBMIT_QUESTION");
    setAdditionalNotes("");
    setUrgency("NORMAL");
    setCreatedTicket(null);
    setErrorMessage(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-xl w-full p-5 sm:p-6 space-y-4 relative max-h-[92vh] overflow-y-auto custom-scrollbar">
        <button
          onClick={handleReset}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="Close Modal"
        >
          <X className="w-5 h-5" />
        </button>

        {createdTicket ? (
          <div className="text-center py-6 space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300 flex items-center justify-center mx-auto shadow-inner">
              <CheckCircle2 className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Escalation Ticket Dispatched
              </h3>
              <p className="text-xs text-slate-500 mt-1.5 max-w-sm mx-auto">
                Assigned Ticket ID <code className="font-mono text-emerald-700 dark:text-emerald-400 font-bold bg-emerald-50 dark:bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-200 dark:border-emerald-800">#{createdTicket.id.slice(0, 8).toUpperCase()}</code>.
              </p>
              <p className="text-[11px] text-slate-400 mt-2 max-w-md mx-auto">
                An accredited Ministry / AIIA IP facilitator will examine the statutory provisions, ABS requirements, and formulation context.
              </p>
            </div>
            <div className="flex items-center justify-center gap-2.5 pt-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                className="text-xs"
              >
                Back to Consultation
              </Button>
              <Button
                size="sm"
                onClick={() => {
                  handleReset();
                  navigate("/facilitator-desk");
                }}
                className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold"
              >
                Track in Facilitator Desk →
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Header */}
            <div className="flex items-center gap-2.5 text-emerald-800 dark:text-emerald-400 border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600">
                <HelpCircle className="w-5 h-5 shrink-0" />
              </div>
              <div>
                <h3 className="font-bold text-base text-slate-900 dark:text-white">
                  IP Facilitator Escalation Desk
                </h3>
                <p className="text-[11px] text-slate-500">
                  Human statutory verification & compliance review
                </p>
              </div>
            </div>

            {errorMessage && (
              <div className="p-2.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* 1. Autofilled Product Context Card */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 flex items-center gap-1">
                  <Sparkles className="w-3 h-3" />
                  Product Formulation (Autofilled)
                </span>
                <span className="text-[10px] bg-emerald-100 dark:bg-emerald-900/50 text-emerald-800 dark:text-emerald-300 px-1.5 py-0.2 rounded font-semibold">
                  {productCategory}
                </span>
              </div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                {productName}
              </p>
              <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-2 leading-relaxed">
                {productDetails}
              </p>
            </div>

            {/* 2. Autofilled Question & Generated Answer */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Question */}
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200/80 dark:border-slate-800 space-y-1">
                <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                  <User className="w-3 h-3 text-slate-400" />
                  Question Asked (Autofilled)
                </span>
                <p className="text-xs font-medium text-slate-800 dark:text-slate-200 line-clamp-3 italic">
                  "{userQuery || "No prior query recorded"}"
                </p>
              </div>

              {/* Generated Answer with Confidence */}
              <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-950/50 border border-slate-200/80 dark:border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                    <Bot className="w-3 h-3 text-emerald-600" />
                    AI Response
                  </span>
                  <ConfidenceBadge
                    score={confidenceScore}
                    label={(confidenceLabel as any) || "LOW"}
                    requiresReview={true}
                  />
                </div>
                <p className="text-[11px] text-slate-600 dark:text-slate-400 line-clamp-3 leading-snug">
                  {assistantResponse || "Response under review"}
                </p>
              </div>
            </div>

            {/* 3. Escalation Request Type Options */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
                Select Request Type:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {ESCALATION_OPTIONS.map((opt) => {
                  const Icon = opt.icon;
                  const isSelected = selectedCategory === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setSelectedCategory(opt.id)}
                      className={`p-2 rounded-xl border cursor-pointer transition-all flex items-start gap-2 ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50/70 dark:bg-emerald-950/50 shadow-2xs"
                          : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      }`}
                    >
                      <div className={`p-1.5 rounded-lg mt-0.5 shrink-0 ${isSelected ? "bg-emerald-700 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                        <Icon className="w-3 h-3" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className={`text-[11px] font-bold block leading-tight truncate ${isSelected ? "text-emerald-900 dark:text-emerald-200" : "text-slate-800 dark:text-slate-200"}`}>
                          {opt.label}
                        </span>
                        <span className="text-[10px] text-slate-500 block leading-tight mt-0.5 line-clamp-2">
                          {opt.desc}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 4. Additional Questions & Inquiries Section (Editable) */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                <span>Additional Information / Specific Questions for Facilitator</span>
                <span className="text-[10px] text-slate-400 font-normal">Optional</span>
              </label>
              <textarea
                rows={3}
                value={additionalNotes}
                onChange={(e) => setAdditionalNotes(e.target.value)}
                placeholder="Enter any additional details, specific sections to review, commercial export countries, or questions you want to ask the IP facilitator..."
                className="w-full p-2.5 text-xs rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500/40 leading-relaxed custom-scrollbar"
              />
            </div>

            {/* 5. Urgency Selection & Submit Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-1.5">
                <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                  Urgency:
                </span>
                {(["NORMAL", "HIGH", "URGENT"] as const).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setUrgency(lvl)}
                    className={`py-1 px-2.5 text-[10px] rounded-lg border text-center transition-all ${
                      urgency === lvl
                        ? "border-emerald-600 bg-emerald-100/80 dark:bg-emerald-900/60 text-emerald-900 dark:text-emerald-200 font-bold shadow-2xs"
                        : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>

              <div className="flex items-center justify-end gap-2">
                <Button type="button" variant="ghost" size="sm" onClick={handleReset} className="text-xs text-slate-500 h-8">
                  Cancel
                </Button>
                <Button type="submit" size="sm" disabled={isLoading} className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs h-8 font-semibold shadow-xs">
                  {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
                  Submit to Facilitator
                </Button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
