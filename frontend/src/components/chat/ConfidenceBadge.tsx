import React from "react";
import { ShieldCheck, AlertTriangle, AlertOctagon } from "lucide-react";
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
  let pct: number;
  if (score !== undefined && score !== null) {
    pct = score <= 1 ? Math.round(score * 100) : Math.round(score);
  } else {
    pct = label === "HIGH" ? 94 : label === "MEDIUM" ? 72 : 45;
  }

  if (requiresReview || label === "LOW") {
    return (
      <span
        title={`Grounding Confidence Score: ${pct}%`}
        style={{
          backgroundColor: "var(--chip-confidence-low-bg, #FCEBEB)",
          color: "var(--chip-confidence-low-text, #791F1F)",
          borderRadius: "6px",
          padding: "3px 8px",
          fontSize: "10px",
          fontWeight: 600,
        }}
        className="inline-flex items-center gap-1 shadow-xs border border-red-200/50"
      >
        <AlertTriangle className="w-3 h-3 shrink-0" />
        <span>Confidence: LOW ({pct}%)</span>
      </span>
    );
  }

  if (label === "MEDIUM") {
    return (
      <span
        title={`Grounding Confidence Score: ${pct}%`}
        style={{
          backgroundColor: "var(--chip-confidence-medium-bg, #FAEEDA)",
          color: "var(--chip-confidence-medium-text, #854F0B)",
          borderRadius: "6px",
          padding: "3px 8px",
          fontSize: "10px",
          fontWeight: 600,
        }}
        className="inline-flex items-center gap-1 shadow-xs border border-amber-200/50"
      >
        <AlertOctagon className="w-3 h-3 shrink-0" />
        <span>Confidence: MEDIUM ({pct}%)</span>
      </span>
    );
  }

  return (
    <span
      title={`Grounding Confidence Score: ${pct}%`}
      style={{
        backgroundColor: "var(--chip-confidence-high-bg, #F0FBE9)",
        color: "var(--chip-confidence-high-text, #3B6D11)",
        borderRadius: "6px",
        padding: "3px 8px",
        fontSize: "10px",
        fontWeight: 600,
      }}
      className="inline-flex items-center gap-1 shadow-xs border border-emerald-200/50"
    >
      <ShieldCheck className="w-3 h-3 shrink-0" />
      <span>Confidence: HIGH ({pct}%)</span>
    </span>
  );
};
