import React from "react";
import { ShieldCheck, AlertTriangle, AlertOctagon } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ConfidenceLabel } from "@/types";

interface ConfidenceBadgeProps {
  score?: number;
  label?: ConfidenceLabel;
  requiresReview?: boolean;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  label = "HIGH",
  requiresReview = false,
}) => {
  if (requiresReview || label === "LOW") {
    return (
      <Badge
        variant="outline"
        className="bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800 gap-1 text-[11px] font-medium"
      >
        <AlertTriangle className="w-3 h-3 text-rose-600" />
        Low Grounding ({score ? `${Math.round(score * 100)}%` : "Review Needed"})
      </Badge>
    );
  }

  if (label === "MEDIUM") {
    return (
      <Badge
        variant="outline"
        className="bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800 gap-1 text-[11px] font-medium"
      >
        <AlertOctagon className="w-3 h-3 text-amber-600" />
        Moderate Grounding ({score ? `${Math.round(score * 100)}%` : "Medium"})
      </Badge>
    );
  }

  return (
    <Badge
      variant="outline"
      className="bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800 gap-1 text-[11px] font-medium"
    >
      <ShieldCheck className="w-3 h-3 text-emerald-600" />
      Evidence-Grounded ({score ? `${Math.round(score * 100)}%` : "High"})
    </Badge>
  );
};
