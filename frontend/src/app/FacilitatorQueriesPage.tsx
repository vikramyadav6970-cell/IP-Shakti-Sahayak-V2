import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import {
  CheckCircle2,
  Clock,
  Search,
  RefreshCw,
  PlusCircle,
  MessageSquare,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  UserCheck,
  ChevronRight,
  Copy,
  Check,
  Sparkles,
  ArrowRight,
  FileText,
  Loader2,
} from "lucide-react";
import { expertService, ExpertRequestItem } from "@/services/expertService";
import { ExpertEscalationModal } from "@/components/chat/ExpertEscalationModal";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export const FacilitatorQueriesPage: React.FC = () => {
  const [requests, setRequests] = useState<ExpertRequestItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [isNewQueryModalOpen, setIsNewQueryModalOpen] = useState(false);
  const [expandedRequestId, setExpandedRequestId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    fetchMyRequests();
  }, []);

  const fetchMyRequests = async (isManualRefresh = false) => {
    if (isManualRefresh) setIsRefreshing(true);
    else setIsLoading(true);

    try {
      const data = await expertService.getMyRequests();
      setRequests(data || []);
      // If there is at least one request and none expanded, auto-expand the first one
      if (data && data.length > 0 && !expandedRequestId) {
        setExpandedRequestId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load user expert requests", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Metrics computation
  const totalCount = requests.length;
  const openCount = requests.filter((r) => r.status === "OPEN").length;
  const inProgressCount = requests.filter((r) => r.status === "IN_PROGRESS").length;
  const resolvedCount = requests.filter((r) => r.status === "RESOLVED").length;

  // Filtered list
  const filteredRequests = requests.filter((r) => {
    const matchesStatus =
      statusFilter === "ALL" || r.status === statusFilter;
    const matchesSearch =
      !searchQuery.trim() ||
      r.context.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (r.response && r.response.toLowerCase().includes(searchQuery.toLowerCase())) ||
      r.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: "OPEN" | "IN_PROGRESS" | "RESOLVED") => {
    switch (status) {
      case "RESOLVED":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            Resolved & Answered
          </span>
        );
      case "IN_PROGRESS":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-300 dark:border-blue-800">
            <Clock className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 animate-spin" />
            Under Legal Review
          </span>
        );
      case "OPEN":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
            <AlertCircle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
            Awaiting Facilitator
          </span>
        );
    }
  };

  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  // Parse [Category: ...] prefix if present in context
  const parseQueryContext = (raw: string) => {
    const match = raw.match(/^\[Category:\s*(.+?)\]\s*\n?([\s\S]*)$/i);
    if (match) {
      return { category: match[1], text: match[2].trim() };
    }
    return { category: "General Inquiry", text: raw.trim() };
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 font-sans">
      {/* 1. Page Header & Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-700 dark:text-emerald-400 mb-1">
            <UserCheck className="w-4 h-4" />
            <span>INSTITUTIONAL HUMAN IP DESK</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            Human IP Facilitator Desk
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1 max-w-2xl">
            Track statutory inquiries, status updates, and customized advisory notes delivered directly by Ministry of Ayush & AIIA accredited IP facilitators.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchMyRequests(true)}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Button
            onClick={() => setIsNewQueryModalOpen(true)}
            className="bg-emerald-700 hover:bg-emerald-800 text-white flex items-center gap-2 text-sm font-semibold shadow-sm shadow-emerald-700/20"
          >
            <PlusCircle className="w-4 h-4" />
            Ask Human IP Facilitator
          </Button>
        </div>
      </div>

      {/* 2. KPI Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Inquiries</p>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">{totalCount}</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300">
              <FileText className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-amber-200/80 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/20 shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">Awaiting Assignment</p>
              <h3 className="text-2xl font-bold text-amber-900 dark:text-amber-200 mt-1">{openCount}</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center text-amber-700 dark:text-amber-300">
              <AlertCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-blue-200/80 dark:border-blue-900/40 bg-blue-50/40 dark:bg-blue-950/20 shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-blue-700 dark:text-blue-400">Under Legal Review</p>
              <h3 className="text-2xl font-bold text-blue-900 dark:text-blue-200 mt-1">{inProgressCount}</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-blue-700 dark:text-blue-300">
              <Clock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border border-emerald-200/80 dark:border-emerald-900/40 bg-emerald-50/40 dark:bg-emerald-950/20 shadow-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-emerald-700 dark:text-emerald-400">Resolved with Notes</p>
              <h3 className="text-2xl font-bold text-emerald-900 dark:text-emerald-200 mt-1">{resolvedCount}</h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center text-emerald-700 dark:text-emerald-300">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 3. Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        {/* Search */}
        <div className="relative w-full sm:w-96">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search queries, legal keywords, or ticket ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-950/60 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: "ALL", label: `All (${totalCount})` },
            { id: "OPEN", label: `Awaiting (${openCount})` },
            { id: "IN_PROGRESS", label: `In Review (${inProgressCount})` },
            { id: "RESOLVED", label: `Resolved (${resolvedCount})` },
          ].map((pill) => (
            <button
              key={pill.id}
              type="button"
              onClick={() => setStatusFilter(pill.id)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                statusFilter === pill.id
                  ? "bg-emerald-700 text-white shadow-xs"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              {pill.label}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Requests List View */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mx-auto" />
          <p className="text-sm font-medium text-slate-500">Loading your facilitator inquiries...</p>
        </div>
      ) : filteredRequests.length === 0 ? (
        <Card className="border border-dashed border-slate-300 dark:border-slate-700 bg-white/50 dark:bg-slate-900/50 p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 flex items-center justify-center text-emerald-600 mx-auto mb-4">
            <HelpCircle className="w-7 h-7" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">
            {requests.length === 0 ? "No Facilitator Inquiries Yet" : "No Matching Inquiries Found"}
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 mb-6">
            {requests.length === 0
              ? "Have a complex patentability §3(p) question, need ABS compliance clarity, or want human legal review of your Ayurvedic formulation? Submit your first question to our accredited IP facilitators."
              : "Try adjusting your search filters or status selection to find what you're looking for."}
          </p>
          {requests.length === 0 ? (
            <Button
              onClick={() => setIsNewQueryModalOpen(true)}
              className="bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs inline-flex items-center gap-2"
            >
              <PlusCircle className="w-4 h-4" />
              Ask Human IP Facilitator
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setStatusFilter("ALL");
                setSearchQuery("");
              }}
            >
              Clear Filters
            </Button>
          )}
        </Card>
      ) : (
        <div className="space-y-4">
          {filteredRequests.map((item) => {
            const isExpanded = expandedRequestId === item.id;
            const parsed = parseQueryContext(item.context);

            return (
              <Card
                key={item.id}
                className={`border transition-all duration-200 overflow-hidden ${
                  item.status === "RESOLVED"
                    ? "border-emerald-200 dark:border-emerald-900/50 bg-white dark:bg-slate-900 shadow-xs"
                    : item.status === "IN_PROGRESS"
                    ? "border-blue-200 dark:border-blue-900/50 bg-white dark:bg-slate-900 shadow-xs"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs"
                }`}
              >
                {/* Header Strip / Summary */}
                <div
                  onClick={() => setExpandedRequestId(isExpanded ? null : item.id)}
                  className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <div className="space-y-1.5 flex-1 min-w-0 pr-4">
                    <div className="flex items-center gap-2.5 flex-wrap">
                      <span className="text-[11px] font-mono font-bold text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded">
                        TICKET #{item.id.slice(0, 8).toUpperCase()}
                      </span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                        {parsed.category}
                      </span>
                      {getStatusBadge(item.status)}
                    </div>

                    <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100 truncate mt-1">
                      {parsed.text}
                    </h3>

                    <p className="text-[11px] text-slate-400">
                      Submitted on {formatDate(item.created_at)}
                      {item.updated_at !== item.created_at && (
                        <span> • Last updated {formatDate(item.updated_at)}</span>
                      )}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedRequestId(isExpanded ? null : item.id);
                      }}
                      className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 flex items-center gap-1 hover:underline"
                    >
                      <span>{isExpanded ? "Hide Details" : "View Updates"}</span>
                      <ChevronRight
                        className={`w-4 h-4 transition-transform duration-200 ${
                          isExpanded ? "rotate-90" : ""
                        }`}
                      />
                    </button>
                  </div>
                </div>

                {/* Expanded Details / Facilitator Response */}
                {isExpanded && (
                  <div className="border-t border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/40 p-4 sm:p-6 space-y-6">
                    {/* Stepper Progress Indicator */}
                    <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-3">
                        Review Workflow Status
                      </span>
                      <div className="grid grid-cols-3 gap-2 text-center text-xs">
                        <div className="flex flex-col items-center">
                          <div className="w-7 h-7 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold text-xs mb-1.5">
                            ✓
                          </div>
                          <span className="font-semibold text-slate-900 dark:text-slate-100">1. Query Submitted</span>
                          <span className="text-[10px] text-slate-400">Logged in queue</span>
                        </div>

                        <div className="flex flex-col items-center">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs mb-1.5 ${
                              item.status === "IN_PROGRESS" || item.status === "RESOLVED"
                                ? "bg-emerald-600 text-white"
                                : "bg-slate-200 dark:bg-slate-800 text-slate-400"
                            }`}
                          >
                            {item.status === "IN_PROGRESS" || item.status === "RESOLVED" ? "✓" : "2"}
                          </div>
                          <span
                            className={`font-semibold ${
                              item.status === "IN_PROGRESS" || item.status === "RESOLVED"
                                ? "text-slate-900 dark:text-slate-100"
                                : "text-slate-400"
                            }`}
                          >
                            2. Facilitator Review
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {item.status === "OPEN" ? "Pending assignment" : "Expert analyzing corpus"}
                          </span>
                        </div>

                        <div className="flex flex-col items-center">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs mb-1.5 ${
                              item.status === "RESOLVED"
                                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/30"
                                : "bg-slate-200 dark:bg-slate-800 text-slate-400"
                            }`}
                          >
                            {item.status === "RESOLVED" ? "✓" : "3"}
                          </div>
                          <span
                            className={`font-semibold ${
                              item.status === "RESOLVED"
                                ? "text-emerald-700 dark:text-emerald-400 font-bold"
                                : "text-slate-400"
                            }`}
                          >
                            3. Advisory Delivered
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {item.status === "RESOLVED" ? "Resolution published" : "Awaiting final sign-off"}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Section 1: User's Original Query */}
                    <div className="space-y-2">
                      <span className="text-xs font-bold text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                        <MessageSquare className="w-3.5 h-3.5 text-slate-500" />
                        YOUR INQUIRY & SUBMITTED CONTEXT:
                      </span>
                      <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                        <p className="whitespace-pre-wrap">{parsed.text}</p>
                      </div>
                    </div>

                    {/* Section 2: Facilitator's Official Response (If Resolved) */}
                    {item.response ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-emerald-800 dark:text-emerald-400 flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-emerald-600" />
                            OFFICIAL FACILITATOR RESOLUTION & ADVISORY NOTES:
                          </span>
                          <button
                            type="button"
                            onClick={() => handleCopy(item.response || "", item.id)}
                            className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-emerald-700 dark:hover:text-emerald-300"
                          >
                            {copiedId === item.id ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                                <span className="text-emerald-600">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span>Copy Advisory</span>
                              </>
                            )}
                          </button>
                        </div>

                        <div className="p-5 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800 text-sm text-slate-900 dark:text-slate-100 leading-relaxed shadow-xs space-y-3">
                          <ReactMarkdown
                            components={{
                              h1: ({ node, ...props }) => <h1 className="text-base font-bold text-emerald-900 dark:text-emerald-200 mt-2 mb-1" {...props} />,
                              h2: ({ node, ...props }) => <h2 className="text-sm font-bold text-emerald-900 dark:text-emerald-200 mt-2 mb-1" {...props} />,
                              h3: ({ node, ...props }) => <h3 className="text-sm font-bold text-emerald-800 dark:text-emerald-300 mt-2 mb-1" {...props} />,
                              p: ({ node, ...props }) => <p className="mb-2 leading-relaxed text-sm last:mb-0" {...props} />,
                              strong: ({ node, ...props }) => <strong className="font-bold text-emerald-950 dark:text-emerald-100" {...props} />,
                              ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1 text-sm text-slate-800 dark:text-slate-200" {...props} />,
                              ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1 text-sm text-slate-800 dark:text-slate-200" {...props} />,
                              li: ({ node, ...props }) => <li className="leading-relaxed" {...props} />,
                              hr: ({ node, ...props }) => <hr className="my-2.5 border-emerald-200 dark:border-emerald-800" {...props} />,
                              blockquote: ({ node, ...props }) => (
                                <blockquote className="pl-3 border-l-2 border-emerald-600 italic text-emerald-900 dark:text-emerald-300 my-2 bg-emerald-100/40 dark:bg-emerald-900/20 p-2 rounded-r" {...props} />
                              ),
                            }}
                          >
                            {item.response}
                          </ReactMarkdown>

                          <div className="pt-3 border-t border-emerald-200/80 dark:border-emerald-800/80 flex items-center justify-between text-xs text-emerald-800 dark:text-emerald-300">
                            <span className="flex items-center gap-1 font-semibold">
                              <UserCheck className="w-3.5 h-3.5" />
                              Accredited Ayurvedic IP Facilitator Desk
                            </span>
                            <span>Signed & Resolved: {formatDate(item.updated_at)}</span>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 flex items-start gap-3">
                        <Clock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                        <div className="space-y-1 text-xs">
                          <h4 className="font-bold text-amber-900 dark:text-amber-200">
                            Advisory In Preparation
                          </h4>
                          <p className="text-amber-800 dark:text-amber-300 leading-relaxed">
                            Your inquiry has been logged in the active facilitator queue. An accredited IP specialist is cross-referencing your formulation against TKDL prior-art indices and statutory provisions. You will see their written resolution here once completed.
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Bottom Actions */}
                    <div className="flex items-center justify-between pt-2">
                      <Link
                        to="/chat"
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 hover:underline"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Continue Conversation in AI Assistant</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>

                      <span className="text-[11px] text-slate-400 font-mono">
                        Ref: {item.id}
                      </span>
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Direct Escalation / New Inquiry Modal */}
      <ExpertEscalationModal
        isOpen={isNewQueryModalOpen}
        onClose={() => {
          setIsNewQueryModalOpen(false);
          fetchMyRequests(true);
        }}
      />
    </div>
  );
};
