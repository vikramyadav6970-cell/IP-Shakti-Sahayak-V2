import React, { useEffect, useState } from "react";
import {
  Package,
  Plus,
  Search,
  Trash2,
  X,
  Loader2,
  CheckCircle2,
  Scale,
  AlertCircle,
  FlaskConical,
} from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { Button } from "@/components/ui/button";

export const ProductHistorySidebar: React.FC = () => {
  const {
    conversations,
    activeConversationId,
    isHistoryOpen,
    isLoadingHistory,
    toggleHistory,
    fetchConversations,
    loadConversation,
    deleteConversation,
    startNewConsultation,
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>("ALL");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (isHistoryOpen) {
      fetchConversations();
    }
  }, [isHistoryOpen, fetchConversations]);

  if (!isHistoryOpen) return null;

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this product consultation dossier?")) {
      setDeletingId(id);
      try {
        await deleteConversation(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  // Filter products by category and search text
  const filteredProducts = conversations.filter((c) => {
    // Category match
    const categoryKey = (c.category || "").toUpperCase();
    let matchesCategory = true;
    if (selectedCategoryFilter === "CLASSICAL") {
      matchesCategory = categoryKey.includes("CLASSICAL");
    } else if (selectedCategoryFilter === "PROPRIETARY") {
      matchesCategory = categoryKey.includes("PROPRIETARY");
    } else if (selectedCategoryFilter === "AAHARA") {
      matchesCategory = categoryKey.includes("AAHARA") || categoryKey.includes("FOOD");
    } else if (selectedCategoryFilter === "PHYTOPHARMA") {
      matchesCategory = categoryKey.includes("PHYTO") || categoryKey.includes("DRUG");
    } else if (selectedCategoryFilter === "COSMETIC") {
      matchesCategory = categoryKey.includes("COSMETIC");
    } else if (selectedCategoryFilter === "DRAFT") {
      matchesCategory = !c.category || c.classification_state !== "CLASSIFIED";
    }

    // Search query match (searches product name, ingredients, category, dosage form)
    let matchesSearch = true;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const nameMatch = (c.product_name || c.title || "").toLowerCase().includes(q);
      const catMatch = (c.category_name || c.category || "").toLowerCase().includes(q);
      const ingMatch = (c.ingredients || []).some((ing) => ing.toLowerCase().includes(q));
      const dosageMatch = (c.dosage_form || "").toLowerCase().includes(q);
      matchesSearch = nameMatch || catMatch || ingMatch || dosageMatch;
    }

    return matchesCategory && matchesSearch;
  });

  const getCategoryColor = (cat?: string) => {
    const k = (cat || "").toUpperCase();
    if (k.includes("CLASSICAL")) {
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800";
    }
    if (k.includes("PROPRIETARY")) {
      return "bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border-blue-300 dark:border-blue-800";
    }
    if (k.includes("AAHARA")) {
      return "bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-300 dark:border-amber-800";
    }
    if (k.includes("PHYTO") || k.includes("DRUG")) {
      return "bg-purple-100 text-purple-800 dark:bg-purple-950/60 dark:text-purple-300 border-purple-300 dark:border-purple-800";
    }
    if (k.includes("COSMETIC")) {
      return "bg-teal-100 text-teal-800 dark:bg-teal-950/60 dark:text-teal-300 border-teal-300 dark:border-teal-800";
    }
    return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700";
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden font-sans">
      {/* Backdrop */}
      <div
        onClick={() => toggleHistory(false)}
        className="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity duration-300 animate-in fade-in"
      />

      <div className="absolute inset-y-0 left-0 max-w-full flex pr-6 sm:pr-10">
        <div className="w-screen max-w-md bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col z-10 animate-in slide-in-from-left duration-300">
          {/* 1. Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/80 dark:bg-slate-950/70">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 text-white flex items-center justify-center shadow-md shadow-emerald-700/20">
                <Package className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
                  Product Formulation History
                </h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400">
                  {conversations.length} formulation dossier{conversations.length === 1 ? "" : "s"}
                </p>
              </div>
            </div>

            <button
              onClick={() => toggleHistory(false)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* 2. New Product Consultation Action Button */}
          <div className="p-3 border-b border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900">
            <Button
              onClick={() => {
                startNewConsultation();
                toggleHistory(false);
              }}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs py-2"
            >
              <Plus className="w-4 h-4" />
              Consult on New Product / Formulation
            </Button>
          </div>

          {/* 3. Search Bar */}
          <div className="p-3 border-b border-slate-200/60 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-950/40">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search by product name, herb, dosage..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>

            {/* Category Filter Pills */}
            <div className="flex items-center gap-1.5 mt-2.5 overflow-x-auto pb-1 text-[11px] scrollbar-none">
              {[
                { id: "ALL", label: "All Products" },
                { id: "CLASSICAL", label: "Classical" },
                { id: "PROPRIETARY", label: "Proprietary" },
                { id: "AAHARA", label: "Aahara" },
                { id: "PHYTOPHARMA", label: "Phytopharma" },
                { id: "COSMETIC", label: "Cosmetic" },
                { id: "DRAFT", label: "In Progress" },
              ].map((pill) => (
                <button
                  key={pill.id}
                  type="button"
                  onClick={() => setSelectedCategoryFilter(pill.id)}
                  className={`px-2 py-1 rounded-md font-medium whitespace-nowrap transition-all ${
                    selectedCategoryFilter === pill.id
                      ? "bg-emerald-700 text-white shadow-xs"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                >
                  {pill.label}
                </button>
              ))}
            </div>
          </div>

          {/* 4. Products List View */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
            {isLoadingHistory ? (
              <div className="py-16 text-center space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
                <p className="text-xs text-slate-500">Loading product dossiers...</p>
              </div>
            ) : filteredProducts.length === 0 ? (
              <div className="py-16 text-center space-y-3 text-slate-400">
                <FlaskConical className="w-10 h-10 mx-auto stroke-1 text-slate-300 dark:text-slate-600" />
                <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                  {conversations.length === 0 ? "No Product Consultations Yet" : "No Matching Products Found"}
                </p>
                <p className="text-[11px] text-slate-500 max-w-xs mx-auto leading-relaxed">
                  Start a new consultation and your product formulation, statutory category, patentability evaluation, and citations will be cataloged here.
                </p>
              </div>
            ) : (
              filteredProducts.map((item) => {
                const isActive = activeConversationId === item.id;
                const displayName = item.product_name || item.title || "Ayurvedic Product Formulation";
                const displayCategory = item.category_name || item.category || "Unclassified Formulation";

                return (
                  <div
                    key={item.id}
                    onClick={() => loadConversation(item.id)}
                    className={`group relative p-3.5 rounded-xl border text-left cursor-pointer transition-all duration-150 space-y-2 ${
                      isActive
                        ? "bg-emerald-50/90 dark:bg-emerald-950/50 border-emerald-400 dark:border-emerald-700 shadow-sm"
                        : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:bg-slate-50/80 dark:hover:bg-slate-800/60 hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                  >
                    {/* Header: Name + Active indicator + Delete */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2 min-w-0 flex-1">
                        <div className="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 dark:text-emerald-300 shrink-0 mt-0.5">
                          <FlaskConical className="w-3.5 h-3.5" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5">
                            {isActive && (
                              <span className="w-2 h-2 rounded-full bg-emerald-600 shrink-0 animate-pulse" />
                            )}
                            <h3
                              className={`text-xs font-bold truncate leading-tight ${
                                isActive
                                  ? "text-emerald-950 dark:text-emerald-100"
                                  : "text-slate-900 dark:text-slate-100"
                              }`}
                            >
                              {displayName}
                            </h3>
                          </div>

                          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${getCategoryColor(
                                item.category
                              )}`}
                            >
                              {item.category ? (
                                <CheckCircle2 className="w-2.5 h-2.5" />
                              ) : (
                                <AlertCircle className="w-2.5 h-2.5" />
                              )}
                              {displayCategory}
                            </span>

                            {item.dosage_form && (
                              <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium">
                                {item.dosage_form}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Delete Button */}
                      <button
                        type="button"
                        onClick={(e) => handleDelete(e, item.id)}
                        disabled={deletingId === item.id}
                        className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                        title="Delete product dossier"
                      >
                        {deletingId === item.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-500" />
                        ) : (
                          <Trash2 className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>

                    {/* Ingredients Chips if present */}
                    {item.ingredients && item.ingredients.length > 0 && (
                      <div className="flex items-center gap-1 flex-wrap pt-0.5">
                        {item.ingredients.slice(0, 3).map((ing, idx) => (
                          <span
                            key={idx}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60 truncate max-w-[120px]"
                          >
                            {ing}
                          </span>
                        ))}
                        {item.ingredients.length > 3 && (
                          <span className="text-[9px] text-slate-400">
                            +{item.ingredients.length - 3} more
                          </span>
                        )}
                      </div>
                    )}

                    {/* Footer: Patent status snapshot & timestamp */}
                    <div className="pt-1.5 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <Scale className="w-3 h-3 text-slate-400" />
                        {item.patent_eligibility
                          ? `Patent: ${item.patent_eligibility}`
                          : `${item.message_count || 1} consultation turns`}
                      </span>

                      <span>{formatDate(item.updated_at || item.created_at)}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
