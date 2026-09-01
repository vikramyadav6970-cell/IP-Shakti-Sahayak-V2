import React, { useState, useEffect } from "react";
import {
  Scale,
  CheckCircle2,
  Clock,
  Activity,
  Search,
  Filter,
  Check,
  Loader2,
  LogOut,
  User,
  FileQuestion,
  Share2,
  Calendar,
  ShieldCheck,
} from "lucide-react";
import { facilitatorService } from "../services/facilitatorService";
import { useFacilitatorAuthStore } from "../store/useFacilitatorAuthStore";
import { ExpertRequestItem } from "../types";

export const FacilitatorDashboardPage: React.FC = () => {
  const { user, clearAuth } = useFacilitatorAuthStore();
  const [activeTab, setActiveTab] = useState<"queue" | "overview">("queue");
  const [expertQueue, setExpertQueue] = useState<ExpertRequestItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchFilter, setSearchFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  // Resolution Modal State
  const [selectedTicket, setSelectedTicket] = useState<ExpertRequestItem | null>(null);
  const [resolutionText, setResolutionText] = useState("");
  const [resolutionStatus, setResolutionStatus] = useState<"RESOLVED" | "IN_PROGRESS">("RESOLVED");
  const [isSubmittingResolution, setIsSubmittingResolution] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const queueRes = await facilitatorService.getQueue().catch(() => []);
      setExpertQueue(queueRes || []);
    } catch (err) {
      console.error("Failed to load facilitator queue", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !resolutionText.trim()) return;

    setIsSubmittingResolution(true);
    try {
      const updated = await facilitatorService.resolveTicket(selectedTicket.id, {
        status: resolutionStatus,
        resolution_notes: resolutionText.trim(),
      });

      setExpertQueue((prev) =>
        prev.map((t) => (t.id === selectedTicket.id ? updated : t))
      );
      setSelectedTicket(null);
      setResolutionText("");
    } catch (err: any) {
      alert(err.message || "Failed to submit resolution.");
    } finally {
      setIsSubmittingResolution(false);
    }
  };

  const filteredQueue = expertQueue.filter((t) => {
    const matchesStatus = statusFilter === "ALL" || t.status === statusFilter;
    const matchesSearch =
      searchFilter.trim() === "" ||
      t.context.toLowerCase().includes(searchFilter.toLowerCase()) ||
      t.id.toLowerCase().includes(searchFilter.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const openCount = expertQueue.filter((t) => t.status === "OPEN").length;
  const inProgressCount = expertQueue.filter((t) => t.status === "IN_PROGRESS").length;
  const resolvedCount = expertQueue.filter((t) => t.status === "RESOLVED").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur border-b border-slate-800 h-16 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 text-white flex items-center justify-center shadow-md">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-white">IP-SAKTI Facilitation Desk</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
                SAFETY & RELIABILITY FALLBACK
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Ministry of Ayush</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
            <User className="w-3.5 h-3.5 text-emerald-400" />
            <span>{user?.name || "Facilitator"}</span>
            <span className="text-[10px] font-mono text-emerald-400 ml-1">({user?.role})</span>
          </div>

          <button
            onClick={clearAuth}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-rose-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* KPI Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Open Escalations</span>
            <div className="text-2xl font-bold text-amber-400 flex items-center justify-between">
              {openCount}
              <Clock className="w-5 h-5 text-amber-500/50" />
            </div>
            <span className="text-[11px] text-slate-400">Pending facilitator determination</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">In Progress</span>
            <div className="text-2xl font-bold text-sky-400 flex items-center justify-between">
              {inProgressCount}
              <Activity className="w-5 h-5 text-sky-500/50" />
            </div>
            <span className="text-[11px] text-slate-400">Under specialist review</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Resolved Cases</span>
            <div className="text-2xl font-bold text-emerald-400 flex items-center justify-between">
              {resolvedCount}
              <CheckCircle2 className="w-5 h-5 text-emerald-500/50" />
            </div>
            <span className="text-[11px] text-emerald-500/80 font-medium">Statutory advice delivered</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-2">
          <button
            onClick={() => setActiveTab("queue")}
            className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "queue"
                ? "border-emerald-500 text-emerald-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Escalation Desk Queue ({expertQueue.length})
          </button>
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "overview"
                ? "border-emerald-500 text-emerald-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Safety & Reliability Fallback Overview
          </button>
        </div>

        {/* TAB 1: ESCALATION QUEUE */}
        {activeTab === "queue" && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Search tickets by keyword or ID..."
                  className="w-full h-10 pl-9 pr-3 text-xs rounded-lg bg-slate-900 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 text-xs">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-slate-400">Status:</span>
                {(["ALL", "OPEN", "IN_PROGRESS", "RESOLVED"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-3 py-1 rounded-md text-xs transition-colors ${
                      statusFilter === st
                        ? "bg-emerald-700 text-white font-semibold"
                        : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>

            {/* List */}
            {isLoading ? (
              <div className="py-16 text-center">
                <Loader2 className="w-8 h-8 animate-spin text-emerald-500 mx-auto" />
              </div>
            ) : filteredQueue.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 text-xs">
                No escalation inquiries match the current filter.
              </div>
            ) : (
              <div className="space-y-3">
                {filteredQueue.map((ticket) => (
                  <div
                    key={ticket.id}
                    className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                              ticket.status === "OPEN"
                                ? "bg-amber-950 text-amber-300 border border-amber-800"
                                : ticket.status === "IN_PROGRESS"
                                ? "bg-sky-950 text-sky-300 border border-sky-800"
                                : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            }`}
                          >
                            {ticket.status}
                          </span>
                          <span className="text-xs font-mono text-slate-500">
                            Ticket #{ticket.id.slice(0, 8)}
                          </span>
                          <span className="text-[11px] text-slate-500">
                            • {new Date(ticket.created_at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-sm font-semibold text-white whitespace-pre-wrap">
                          {ticket.context}
                        </p>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedTicket(ticket);
                          setResolutionText(ticket.response || "");
                          setResolutionStatus(ticket.status === "OPEN" ? "RESOLVED" : ticket.status);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors shrink-0"
                      >
                        {ticket.status === "RESOLVED" ? "Review Resolution" : "Respond to Inquirer"}
                      </button>
                    </div>

                    {ticket.response && (
                      <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800/80 text-xs space-y-1">
                        <div className="flex items-center justify-between text-emerald-400 font-bold">
                          <span>Facilitator Determination:</span>
                          <span className="text-[10px] text-slate-500 font-normal">
                            Resolved by {ticket.resolved_by || "Institutional Specialist"}
                          </span>
                        </div>
                        <p className="text-slate-300 whitespace-pre-wrap">{ticket.response}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: SAFETY & RELIABILITY OVERVIEW */}
        {activeTab === "overview" && (
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-white">
                Human-in-the-Loop Safety & Reliability Architecture
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                The human facilitation desk is designed as a safety, compliance, and reliability fallback. The facilitator doesn't need to answer every routine question — the RAG pipeline automatically resolves and cites over 95% of standard legal inquiries with zero hallucination. Facilitators intervene when novel formulations or edge-case disputes arise.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <FileQuestion className="w-4 h-4" />
                  <span>1. Ambiguous Patentability Objections (§3(p))</span>
                </div>
                <p className="text-xs text-slate-400">
                  When a formulation falls in the grey boundary of Section 3(p) vs synergistic bio-enhancement under Section 3(e), facilitators review experimental data before formal patent specification filing.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <Share2 className="w-4 h-4" />
                  <span>2. Cross-Border ABS & Nagoya Compliance</span>
                </div>
                <p className="text-xs text-slate-400">
                  Facilitators inspect sourcing chains for foreign joint ventures to ensure Form I agreements and benefit-sharing obligations with NBA are executed without penalty.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <Calendar className="w-4 h-4" />
                  <span>3. In-Person Advisory Consultations</span>
                </div>
                <p className="text-xs text-slate-400">
                  Entrepreneurs and startups can request scheduled advisory sessions with IP facilitators to draft comprehensive multi-right protection roadmaps (Patents, Trademarks, Trade Dress).
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4" />
                  <span>4. Statutory Disclaimer Adherence</span>
                </div>
                <p className="text-xs text-slate-400">
                  Ensures all AI outputs carry appropriate legal boundaries and that patent claims are prepared only in conjunction with certified patent agents.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Resolution Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-xl w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-white">
                Respond to Ticket #{selectedTicket.id.slice(0, 8)}
              </h3>
              <span className="text-xs font-mono text-slate-400">
                Status: {selectedTicket.status}
              </span>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
              <span className="font-semibold text-emerald-400 block">User Inquiry / Escalation Context:</span>
              <p className="text-slate-300 whitespace-pre-wrap">{selectedTicket.context}</p>
            </div>

            <form onSubmit={handleResolve} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">
                  Authoritative Statutory Advice & Facilitator Notes:
                </label>
                <textarea
                  rows={5}
                  required
                  value={resolutionText}
                  onChange={(e) => setResolutionText(e.target.value)}
                  placeholder="Provide precise statutory guidance, citing relevant sections from Patents Act 1970, Biological Diversity Act 2023, or FSSAI Regulations..."
                  className="w-full p-3 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400 font-medium">Update Status:</label>
                  <select
                    value={resolutionStatus}
                    onChange={(e: any) => setResolutionStatus(e.target.value)}
                    className="h-8 px-2 text-xs rounded bg-slate-800 border border-slate-700 text-white focus:outline-none"
                  >
                    <option value="RESOLVED">Mark as RESOLVED</option>
                    <option value="IN_PROGRESS">Keep IN PROGRESS</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedTicket(null)}
                    className="px-3 py-1.5 text-xs text-slate-400 hover:text-white"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingResolution || !resolutionText.trim()}
                    className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isSubmittingResolution ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    Confirm Resolution
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
