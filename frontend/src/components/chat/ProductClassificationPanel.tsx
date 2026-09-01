import React, { useState } from "react";
import {
  CheckCircle2,
  Sparkles,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  CircleDot,
  Clock,
  FileCheck2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ProductClassificationMeta, ProductContextData, ClassificationState } from "@/types";

interface ProductClassificationPanelProps {
  activeClassification?: ProductClassificationMeta | null;
  productContext?: ProductContextData | null;
  classificationState: ClassificationState;
  onStartDiagnostic: () => void;
  onResetClassification: () => void;
}

export const ProductClassificationPanel: React.FC<ProductClassificationPanelProps> = ({
  activeClassification,
  productContext,
  classificationState,
  onStartDiagnostic,
  onResetClassification,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const isClassified =
    classificationState === "CLASSIFIED" ||
    Boolean(activeClassification) ||
    Boolean(productContext?.category) ||
    productContext?.state === "CLASSIFIED";

  const hasUserFormulation = Boolean(
    productContext?.product_name ||
    (productContext?.ingredients && productContext.ingredients.length > 0) ||
    productContext?.formulation ||
    productContext?.description
  );

  const isCollecting =
    !isClassified &&
    (classificationState === "COLLECTING_PRODUCT_INFORMATION" || productContext?.state === "COLLECTING_PRODUCT_INFORMATION") &&
    hasUserFormulation;

  const renderFieldValue = (val: string | string[] | undefined | null) => {
    if (!val) return <span className="text-slate-400 italic">Not provided</span>;
    if (Array.isArray(val)) {
      if (val.length === 0) return <span className="text-slate-400 italic">Not provided</span>;
      return <span className="text-slate-200 font-medium">{val.join(", ")}</span>;
    }
    return <span className="text-slate-200 font-medium">{val}</span>;
  };

  return (
    <div className="w-full flex flex-col space-y-3 text-slate-800 dark:text-slate-200 font-sans">
      {/* Main Product Classifier Card (Stateful & Expandable) */}
      <div className="rounded-xl bg-slate-900 text-white border border-slate-800 shadow-md overflow-hidden transition-all">
        {/* Card Header & State Indicator */}
        <div className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-mono tracking-wider text-emerald-400 font-bold uppercase flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Product Classifier
            </span>

            {/* State Indicator */}
            {isClassified ? (
              <Badge className="bg-emerald-600 hover:bg-emerald-600 text-white text-[10px] gap-1 px-2 py-0.5 shadow-xs">
                <CheckCircle2 className="w-3 h-3" />
                Product classified
              </Badge>
            ) : isCollecting ? (
              <Badge className="bg-amber-600/90 hover:bg-amber-600 text-white text-[10px] gap-1 px-2 py-0.5 animate-pulse">
                <Clock className="w-3 h-3" />
                Collecting information...
              </Badge>
            ) : (
              <Badge variant="outline" className="text-slate-400 border-slate-700 bg-slate-800/40 text-[10px] gap-1 px-2 py-0.5">
                <CircleDot className="w-3 h-3 text-slate-400" />
                Awaiting formulation
              </Badge>
            )}
          </div>

          {/* Classification Title or Subtitle */}
          <div>
            <h3 className="text-sm font-bold text-white tracking-tight">
              {isClassified
                ? activeClassification?.category_name || productContext?.category || "Classified Product"
                : isCollecting
                ? productContext?.product_name || "Diagnostic In Progress"
                : "Awaiting Product Formulation"}
            </h3>
            <p className="text-[11px] text-slate-400 mt-0.5">
              {isClassified
                ? `Regulatory pathway: ${activeClassification?.regulatory_pathway || productContext?.regulatory_pathway || "Form 25-D License"}`
                : isCollecting
                ? "The assistant is collecting facts to determine statutory classification."
                : "Share your product formulation or herbs below to initiate automated classification."}
            </p>
          </div>

          {/* Action Bar */}
          <div className="pt-2 flex items-center justify-between border-t border-slate-800/80 text-xs">
            <button
              type="button"
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 font-semibold transition-colors"
            >
              <span>Product Context</span>
              {isDropdownOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {isClassified ? (
              <button
                type="button"
                onClick={onResetClassification}
                className="text-[11px] text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Re-diagnose
              </button>
            ) : (
              <button
                type="button"
                onClick={onStartDiagnostic}
                className="text-[11px] text-slate-400 hover:text-emerald-400 transition-colors flex items-center gap-1"
              >
                <RotateCcw className="w-3 h-3" />
                Restart
              </button>
            )}
          </div>
        </div>

        {/* Expandable Product Context Dropdown */}
        {isDropdownOpen && (
          <div className="px-4 pb-4 pt-2 border-t border-slate-800 bg-slate-950/60 text-xs space-y-2">
            <div className="flex items-center justify-between pb-1 border-b border-slate-800/60">
              <span className="text-[10px] font-mono uppercase text-slate-400 font-bold">
                Collected Structured Context
              </span>
              <FileCheck2 className="w-3.5 h-3.5 text-slate-500" />
            </div>

            <div className="space-y-1.5 text-[11px] max-h-96 overflow-y-auto pr-1">
              <div>
                <span className="text-slate-400 block text-[10px]">Product Name:</span>
                {renderFieldValue(productContext?.product_name || activeClassification?.product_name)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Description:</span>
                {renderFieldValue(productContext?.description)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Formulation:</span>
                {renderFieldValue(productContext?.formulation)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Ingredients:</span>
                {renderFieldValue(productContext?.ingredients)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Dosage Form:</span>
                {renderFieldValue(productContext?.dosage_form)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Intended Use / Purpose:</span>
                {renderFieldValue(productContext?.intended_use)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Therapeutic Claims:</span>
                {renderFieldValue(productContext?.therapeutic_claims)}
              </div>

              <div>
                <span className="text-slate-400 block text-[10px]">Classical Source Reference:</span>
                {renderFieldValue(productContext?.classical_source)}
              </div>

              {productContext?.other_relevant_info && (
                <div>
                  <span className="text-slate-400 block text-[10px]">Other Relevant Context:</span>
                  {renderFieldValue(productContext?.other_relevant_info)}
                </div>
              )}

              <div className="pt-1.5 border-t border-slate-800/80">
                <span className="text-slate-400 block text-[10px]">Classification Verdict:</span>
                {isClassified ? (
                  <span className="text-emerald-400 font-bold">
                    {activeClassification?.category_name || productContext?.category}
                  </span>
                ) : (
                  <span className="text-slate-400 italic">Not determined yet</span>
                )}
              </div>

              {isClassified && (productContext?.classification_reason || activeClassification?.reasoning) && (
                <div>
                  <span className="text-slate-400 block text-[10px]">Classification Reason:</span>
                  <span className="text-slate-300">
                    {productContext?.classification_reason || activeClassification?.reasoning}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
