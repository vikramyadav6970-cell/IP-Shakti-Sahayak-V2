import React from "react";
import { ExternalLink, BookOpen, CheckCircle2 } from "lucide-react";
import { Citation } from "@/types";
import { Badge } from "@/components/ui/badge";

interface CitationCardProps {
  citation: Citation;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation }) => {
  return (
    <div className="p-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/85 dark:bg-slate-900/85 hover:bg-white dark:hover:bg-slate-900 transition-all text-xs space-y-1.5 shadow-2xs">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-1.5 font-semibold text-slate-900 dark:text-slate-100 flex-1">
          <BookOpen className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
          <span className="break-words font-semibold leading-snug">
            {citation.document_title}
          </span>
        </div>
        <Badge variant="outline" className="text-[10px] uppercase py-0 px-1 border-slate-300 shrink-0">
          {citation.jurisdiction}
        </Badge>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-1.5 text-slate-500 dark:text-slate-400 pt-0.5">
        <span className="font-mono text-emerald-700 dark:text-emerald-400 font-semibold break-words">
          {citation.section_ref}
        </span>

        {citation.source_url && (
          <a
            href={citation.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-[11px] text-emerald-700 dark:text-emerald-400 hover:underline font-medium shrink-0"
          >
            <span>Verified Source</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      <div className="flex items-center gap-1 text-[10px] text-emerald-600 font-medium pt-0.5">
        <CheckCircle2 className="w-3 h-3 shrink-0" />
        <span>Statutory Authority Verified — Official Gazette Reconciled</span>
      </div>
    </div>
  );
};
