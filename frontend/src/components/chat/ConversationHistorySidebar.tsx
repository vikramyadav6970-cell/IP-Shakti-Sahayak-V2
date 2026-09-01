import React, { useEffect, useState } from "react";
import {
  History,
  Plus,
  Search,
  MessageSquare,
  Trash2,
  X,
  Tag,
  Loader2,
} from "lucide-react";
import { useChatStore } from "@/store/useChatStore";
import { ConversationSummary } from "@/types";
import { Button } from "@/components/ui/button";

export const ConversationHistorySidebar: React.FC = () => {
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
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    if (isHistoryOpen) {
      fetchConversations();
    }
  }, [isHistoryOpen, fetchConversations]);

  if (!isHistoryOpen) return null;

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this consultation session?")) {
      setDeletingId(id);
      try {
        await deleteConversation(id);
      } finally {
        setDeletingId(null);
      }
    }
  };

  const filteredConversations = conversations.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      (c.title && c.title.toLowerCase().includes(q)) ||
      (c.product_name && c.product_name.toLowerCase().includes(q)) ||
      (c.category && c.category.toLowerCase().includes(q))
    );
  });

  // Group conversations by relative time
  const groupConversations = (items: ConversationSummary[]) => {
    const today: ConversationSummary[] = [];
    const yesterday: ConversationSummary[] = [];
    const lastWeek: ConversationSummary[] = [];
    const older: ConversationSummary[] = [];

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterdayStart = todayStart - 86400000;
    const lastWeekStart = todayStart - 7 * 86400000;

    items.forEach((item) => {
      const itemTime = new Date(item.updated_at || item.created_at).getTime();
      if (itemTime >= todayStart) {
        today.push(item);
      } else if (itemTime >= yesterdayStart) {
        yesterday.push(item);
      } else if (itemTime >= lastWeekStart) {
        lastWeek.push(item);
      } else {
        older.push(item);
      }
    });

    return [
      { label: "Today", items: today },
      { label: "Yesterday", items: yesterday },
      { label: "Previous 7 Days", items: lastWeek },
      { label: "Older Sessions", items: older },
    ].filter((g) => g.items.length > 0);
  };

  const groups = groupConversations(filteredConversations);

  const formatTime = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        onClick={() => toggleHistory(false)}
        className="absolute inset-0 bg-black/40 backdrop-blur-xs transition-opacity duration-300 animate-in fade-in"
      />

      <div className="absolute inset-y-0 left-0 max-w-full flex pr-10">
        <div className="w-screen max-w-sm bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col z-10 animate-in slide-in-from-left duration-300">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/70 dark:bg-slate-950/60">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-950 flex items-center justify-center text-emerald-700 dark:text-emerald-300">
                <History className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900 dark:text-white leading-none">
                  Consultation History
                </h2>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  {conversations.length} saved session{conversations.length === 1 ? "" : "s"}
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

          {/* New Consultation Button */}
          <div className="p-3 border-b border-slate-200/80 dark:border-slate-800/80">
            <Button
              onClick={() => {
                startNewConsultation();
                toggleHistory(false);
              }}
              className="w-full bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-xs"
            >
              <Plus className="w-4 h-4" />
              New Consultation Session
            </Button>
          </div>

          {/* Search Box */}
          <div className="p-3 border-b border-slate-200/60 dark:border-slate-800/60">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search history by formulation, topic..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
              />
            </div>
          </div>

          {/* Session List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-4">
            {isLoadingHistory ? (
              <div className="py-12 text-center space-y-2">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-600 mx-auto" />
                <p className="text-xs text-slate-500">Loading your history...</p>
              </div>
            ) : filteredConversations.length === 0 ? (
              <div className="py-12 text-center space-y-2 text-slate-400">
                <MessageSquare className="w-8 h-8 mx-auto stroke-1 text-slate-300 dark:text-slate-600" />
                <p className="text-xs font-medium text-slate-600 dark:text-slate-400">
                  {conversations.length === 0 ? "No consultation sessions yet" : "No matching sessions found"}
                </p>
                <p className="text-[11px] text-slate-400 max-w-xs mx-auto">
                  Your chat conversations, classified formulation states, and citations will be saved here automatically.
                </p>
              </div>
            ) : (
              groups.map((group) => (
                <div key={group.label} className="space-y-1.5">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 py-0.5">
                    {group.label}
                  </div>

                  <div className="space-y-1">
                    {group.items.map((item) => {
                      const isActive = activeConversationId === item.id;
                      return (
                        <div
                          key={item.id}
                          onClick={() => loadConversation(item.id)}
                          className={`group relative p-2.5 rounded-xl border text-left cursor-pointer transition-all duration-150 flex items-start justify-between gap-2 ${
                            isActive
                              ? "bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 shadow-xs"
                              : "bg-white dark:bg-slate-900 border-slate-200/80 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/60"
                          }`}
                        >
                          <div className="min-w-0 flex-1 space-y-1">
                            <div className="flex items-center gap-1.5">
                              {isActive && (
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0" />
                              )}
                              <h4
                                className={`text-xs font-bold truncate leading-tight ${
                                  isActive
                                    ? "text-emerald-900 dark:text-emerald-200"
                                    : "text-slate-800 dark:text-slate-200"
                                }`}
                              >
                                {item.title || item.product_name || "Ayurvedic Consultation"}
                              </h4>
                            </div>

                            <div className="flex items-center gap-1.5 flex-wrap">
                              {item.category && (
                                <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                                  <Tag className="w-2.5 h-2.5" />
                                  {item.category}
                                </span>
                              )}
                              <span className="text-[10px] text-slate-400">
                                {formatTime(item.updated_at || item.created_at)}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                            <button
                              type="button"
                              onClick={(e) => handleDelete(e, item.id)}
                              disabled={deletingId === item.id}
                              className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 transition-colors"
                              title="Delete consultation"
                            >
                              {deletingId === item.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-500" />
                              ) : (
                                <Trash2 className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
