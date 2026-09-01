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
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { expertService, ExpertRequestItem } from "@/services/expertService";

interface ExpertEscalationModalProps {
  isOpen: boolean;
  onClose: () => void;
  messageId?: string;
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
    label: "Submit my question to an IP facilitator",
    desc: "Route query for human legal evaluation when AI response is uncertain or requires human review.",
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
    label: "Share sources / research with facilitator",
    desc: "Send retrieved statutory provisions, monographs, and formulation details for expert dossier check.",
    icon: Share2,
  },
  {
    id: "BOOK_CONSULTATION",
    label: "Book a consultation",
    desc: "Request an advisory session with an institutional Ayurvedic IP facilitator.",
    icon: Calendar,
  },
];

export const ExpertEscalationModal: React.FC<ExpertEscalationModalProps> = ({
  isOpen,
  onClose,
  messageId,
}) => {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<EscalationCategory>("SUBMIT_QUESTION");
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState<"NORMAL" | "HIGH" | "URGENT">("NORMAL");
  const [isLoading, setIsLoading] = useState(false);
  const [createdTicket, setCreatedTicket] = useState<ExpertRequestItem | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) {
      setErrorMessage("Please provide notes or context for the IP facilitator.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const optionLabel = ESCALATION_OPTIONS.find((o) => o.id === selectedCategory)?.label || "";
      const fullContext = `[Category: ${optionLabel}]\n${description.trim()}`;

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
    setDescription("");
    setUrgency("NORMAL");
    setCreatedTicket(null);
    setErrorMessage(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl max-w-lg w-full p-6 space-y-4 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={handleReset}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
        >
          <X className="w-5 h-5" />
        </button>

        {createdTicket ? (
          <div className="text-center py-6 space-y-4">
            <div className="w-12 h-12 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-300 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">Escalation Submitted</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                Your inquiry has been assigned ticket ID <code className="font-mono text-emerald-700 dark:text-emerald-400 font-bold">#{createdTicket.id.slice(0, 8).toUpperCase()}</code> and queued for review on the Human IP Facilitation Desk.
              </p>
              <p className="text-[11px] text-slate-400 mt-2">
                An accredited IP facilitator will review the statutory provisions and post updates to your Facilitator Desk dashboard.
              </p>
            </div>
            <div className="flex items-center justify-center gap-2 pt-2">
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
            <div className="flex items-center gap-2 text-emerald-800 dark:text-emerald-400">
              <HelpCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              <h3 className="font-bold text-base text-slate-900 dark:text-white">
                Human IP Facilitator Desk
              </h3>
            </div>

            <p className="text-xs text-slate-500 leading-relaxed">
              Select your facilitation request type. The human facilitator desk acts as a reliability and compliance fallback for complex statutory determinations.
            </p>

            {errorMessage && (
              <div className="p-2.5 rounded bg-rose-50 dark:bg-rose-950/40 border border-rose-200 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {errorMessage}
              </div>
            )}

            {/* Escalation Options Selection */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300 block">
                Select Request Type:
              </label>
              <div className="space-y-1.5">
                {ESCALATION_OPTIONS.map((opt) => {
                  const Icon = opt.icon;
                  const isSelected = selectedCategory === opt.id;
                  return (
                    <div
                      key={opt.id}
                      onClick={() => setSelectedCategory(opt.id)}
                      className={`p-2.5 rounded-lg border cursor-pointer transition-all flex items-start gap-2.5 ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50/60 dark:bg-emerald-950/40"
                          : "border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      }`}
                    >
                      <div className={`p-1.5 rounded-md mt-0.5 ${isSelected ? "bg-emerald-700 text-white" : "bg-slate-100 dark:bg-slate-800 text-slate-500"}`}>
                        <Icon className="w-3.5 h-3.5" />
                      </div>
                      <div className="flex-1">
                        <span className={`text-xs font-semibold block ${isSelected ? "text-emerald-900 dark:text-emerald-200" : "text-slate-800 dark:text-slate-200"}`}>
                          {opt.label}
                        </span>
                        <span className="text-[11px] text-slate-500 block leading-tight">
                          {opt.desc}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Notes / Details */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Additional Notes / Formulation Context
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Explain the specific statutory provision, patent claim question, or commercial export context requiring facilitator review..."
                className="w-full p-2.5 text-xs rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Urgency */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Urgency Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(["NORMAL", "HIGH", "URGENT"] as const).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setUrgency(lvl)}
                    className={`py-1.5 px-3 text-xs rounded border text-center transition-all ${
                      urgency === lvl
                        ? "border-emerald-600 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-900 dark:text-emerald-200 font-bold"
                        : "border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="ghost" size="sm" onClick={handleReset} className="text-xs text-slate-500">
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={isLoading} className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs">
                {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" /> : null}
                Submit Request
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
