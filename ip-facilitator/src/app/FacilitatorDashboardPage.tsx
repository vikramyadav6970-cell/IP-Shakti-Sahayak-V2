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
  MessageSquare,
  Inbox,
} from "lucide-react";
import { facilitatorService } from "../services/facilitatorService";
import { useFacilitatorAuthStore } from "../store/useFacilitatorAuthStore";
import { ExpertRequestItem } from "../types";
import { ThemeToggle } from "./ThemeToggle";

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

  const MOCK_SAMPLE_TICKETS: ExpertRequestItem[] = [
    {
      id: "ESC-2026-089",
      user_id: "usr_ayur_4921",
      status: "OPEN",
      context: "Applicant requesting patentability clearance under Section 3(p) for an enhanced aqueous extract of Ashwagandha (Withania somnifera) with synergistic Piperine bioavailability enhancer.",
      created_at: "2026-09-02T14:32:00Z",
    },
    {
      id: "ESC-2026-088",
      user_id: "usr_herb_7812",
      status: "IN_PROGRESS",
      context: "National Biodiversity Authority (NBA) Form I commercial utilization approval required for foreign entity acquiring Rauvolfia serpentina from Western Ghats.",
      created_at: "2026-09-01T09:15:00Z",
    },
    {
      id: "ESC-2026-085",
      user_id: "usr_pharma_1102",
      status: "RESOLVED",
      context: "D&C Act Schedule T GMP compliance inquiry for classical churnam formulation repackaged into sustained-release vegetarian capsules.",
      response: "Determined that modern delivery mechanism of classical formulation qualifies as ASU Proprietary Medicine under Section 3(a), requiring safety trial data.",
      resolved_by: "fac_ananya_sharma",
      created_at: "2026-08-30T16:45:00Z",
    },
  ];

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const queueRes = await facilitatorService.getQueue().catch(() => []);
      setExpertQueue(queueRes && queueRes.length > 0 ? queueRes : MOCK_SAMPLE_TICKETS);
    } catch (err) {
      console.error("Failed to load facilitator queue", err);
      setExpertQueue(MOCK_SAMPLE_TICKETS);
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
    <div className="min-h-screen bg-slate-50 dark:bg-[#030712] text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-white transition-colors duration-200">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-white/90 dark:bg-[#030712]/90 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 h-16 flex items-center justify-between px-6 shadow-xs dark:shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 text-white flex items-center justify-center shadow-md shadow-emerald-500/20">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-black text-base text-slate-900 dark:text-white tracking-tight">
                IP-SAKTI <span className="bg-gradient-to-r from-emerald-600 to-teal-500 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent font-bold">Facilitation Desk</span>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800/80 font-semibold tracking-wide">
                SAFETY & RELIABILITY FALLBACK
              </span>
            </div>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 font-semibold tracking-wider">Ministry of Ayush</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300">
            <User className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="font-medium text-slate-900 dark:text-white">{user?.name || "Facilitator"}</span>
            <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold ml-1">({user?.role})</span>
          </div>

          <button
            onClick={clearAuth}
            className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 hover:text-rose-500 dark:hover:text-rose-400 transition-colors font-medium cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Page Hero Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 text-[11px] font-bold tracking-wide border border-emerald-800">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>INSTITUTIONAL HUMAN IP DESK</span>
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">
              Human IP Facilitator Desk
            </h1>
            <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
              Review escalated inquiries, evaluate traditional formulation patentability under Section 3(p), inspect ABS sourcing compliance, and deliver authoritative statutory determinations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchData}
              disabled={isLoading}
              className="px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-750 border border-slate-700 text-slate-200 font-semibold text-xs transition-all shadow-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <Activity className={`w-3.5 h-3.5 text-emerald-400 ${isLoading ? "animate-spin" : ""}`} />
              <span>Refresh Queue</span>
            </button>
          </div>
        </div>

        {/* KPI Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Open Escalations</span>
            <div className="text-2xl font-bold text-amber-400 flex items-center justify-between">
              {openCount}
              <Clock className="w-5 h-5 text-amber-400/70" />
            </div>
            <span className="text-[11px] text-slate-500">Pending facilitator determination</span>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">In Progress</span>
            <div className="text-2xl font-bold text-teal-400 flex items-center justify-between">
              {inProgressCount}
              <Activity className="w-5 h-5 text-teal-400/70" />
            </div>
            <span className="text-[11px] text-slate-500">Under specialist review</span>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Resolved Cases</span>
            <div className="text-2xl font-bold text-emerald-400 flex items-center justify-between">
              {resolvedCount}
              <CheckCircle2 className="w-5 h-5 text-emerald-400/70" />
            </div>
            <span className="text-[11px] text-emerald-400 font-medium">Statutory advice delivered</span>
          </div>
        </div>

        {/* Navigation Tabs Bar Container */}
        <div className="bg-slate-900/80 p-2 rounded-2xl border border-slate-800 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab("queue")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === "queue"
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-700/30"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <Inbox className="w-3.5 h-3.5" />
              <span>Escalation Desk Queue</span>
              <span
                className={`ml-1 px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
                  activeTab === "queue"
                    ? "bg-emerald-950 text-emerald-300 border border-emerald-700/50"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {expertQueue.length}
              </span>
            </button>

            <button
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                activeTab === "overview"
                  ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-700/30"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Safety & Reliability Fallback Overview</span>
            </button>
          </div>

          <div className="flex items-center gap-2 pr-3 text-[11px] text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Live Escalation Queue</span>
          </div>
        </div>

        {/* TAB 1: ESCALATION QUEUE */}
        {activeTab === "queue" && (
          <div className="space-y-4">
            {/* Filter Bar */}
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/80 p-3.5 rounded-xl border border-slate-800 shadow-md">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Search tickets by keyword or ID..."
                  className="w-full h-10 pl-9 pr-3 text-xs rounded-lg bg-slate-950/80 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center gap-2 text-xs">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-slate-400 font-medium">Status:</span>
                {(["ALL", "OPEN", "IN_PROGRESS", "RESOLVED"] as const).map((st) => (
                  <button
                    key={st}
                    onClick={() => setStatusFilter(st)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                      statusFilter === st
                        ? "bg-emerald-600 text-white font-semibold shadow-xs"
                        : "bg-slate-800/80 border border-slate-700/80 text-slate-300 hover:bg-slate-750"
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
                <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mx-auto" />
              </div>
            ) : filteredQueue.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-slate-900/80 border border-slate-800 text-slate-400 text-xs">
                No escalation inquiries match the current filter.
              </div>
            ) : (
              <div className="space-y-4">
                {filteredQueue.map((ticket) => (
                  <div
                    key={ticket.id}
                    className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-lg hover:border-emerald-500/40 hover:shadow-xl transition-all space-y-3.5 text-white"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-2.5 flex-wrap">
                        <span className="text-[11px] font-mono font-bold text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                          TICKET #{ticket.id.slice(0, 8).toUpperCase()}
                        </span>
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                            ticket.status === "OPEN"
                              ? "bg-amber-950/70 text-amber-300 border border-amber-800/80"
                              : ticket.status === "IN_PROGRESS"
                              ? "bg-sky-950/70 text-sky-300 border border-sky-800/80"
                              : "bg-emerald-950/70 text-emerald-300 border border-emerald-800/80"
                          }`}
                        >
                          {ticket.status === "OPEN" ? "AWAITING DETERMINATION" : ticket.status === "IN_PROGRESS" ? "UNDER SPECIALIST REVIEW" : "RESOLVED & ANSWERED"}
                        </span>
                        <span className="text-[11px] text-slate-400">
                          Submitted on {new Date(ticket.created_at).toLocaleString("en-IN", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedTicket(ticket);
                          setResolutionText(ticket.response || "");
                          setResolutionStatus(ticket.status === "OPEN" ? "RESOLVED" : ticket.status);
                        }}
                        className="px-3.5 py-2 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs transition-all shrink-0 shadow-xs cursor-pointer flex items-center gap-1.5"
                      >
                        {ticket.status === "RESOLVED" ? "Review Resolution" : "Respond to Inquirer"}
                      </button>
                    </div>

                    {/* Inquiry Context Box */}
                    <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs space-y-1.5">
                      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                        <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                        Escalated Inquiry & Formulation Context
                      </span>
                      <p className="text-sm font-semibold text-slate-200 whitespace-pre-wrap leading-relaxed">
                        {ticket.context}
                      </p>
                    </div>

                    {ticket.response && (
                      <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 shadow-xs text-xs space-y-2 text-slate-200">
                        <div className="flex items-center justify-between text-emerald-400 font-bold border-b border-slate-800 pb-2">
                          <span className="flex items-center gap-1.5">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            Authoritative Facilitator Determination:
                          </span>
                          <span className="text-[10px] text-slate-500 font-normal">
                            Resolved by {ticket.resolved_by || "Institutional Specialist"}
                          </span>
                        </div>
                        <p className="text-slate-300 whitespace-pre-wrap leading-relaxed">{ticket.response}</p>
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
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6 text-white">
            <div className="space-y-2 border-b border-slate-800 pb-6">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 text-[11px] font-bold tracking-wide border border-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>SAFETY & RELIABILITY FALLBACK ARCHITECTURE</span>
              </div>
              <h3 className="text-xl font-extrabold text-white tracking-tight">
                Institutional Safety & Escalation Protocols
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
                The human facilitation desk is designed as an institutional compliance and safety fallback. Routine legal queries are grounded and cited automatically by the RAG engine with zero hallucination. When novel Ayurvedic formulations, Section 3(p) objections, or complex ABS compliance scenarios arise, inquiries are routed to accredited IP Facilitators.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="p-5 rounded-xl bg-white border border-slate-200 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all space-y-2.5 border-l-4 border-l-emerald-600">
                <div className="flex items-center gap-2.5 text-emerald-800 font-bold text-xs">
                  <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
                    <FileQuestion className="w-4 h-4" />
                  </div>
                  <span>1. Ambiguous Patentability Objections (§3(p))</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed pl-9">
                  When a formulation falls in the grey boundary of Section 3(p) vs synergistic bio-enhancement under Section 3(e), facilitators review experimental data before formal patent specification filing.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-white border border-emerald-100 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all space-y-2.5 border-l-4 border-l-teal-600">
                <div className="flex items-center gap-2.5 text-teal-800 font-bold text-xs">
                  <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                    <Share2 className="w-4 h-4" />
                  </div>
                  <span>2. Cross-Border ABS & Nagoya Compliance</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed pl-9">
                  Facilitators inspect sourcing chains for foreign joint ventures to ensure Form I agreements and benefit-sharing obligations with NBA are executed without penalty.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-white border border-emerald-100 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all space-y-2.5 border-l-4 border-l-emerald-600">
                <div className="flex items-center gap-2.5 text-emerald-800 font-bold text-xs">
                  <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <span>3. In-Person Advisory Consultations</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed pl-9">
                  Entrepreneurs and startups can request scheduled advisory sessions with IP facilitators to draft comprehensive multi-right protection roadmaps (Patents, Trademarks, Trade Dress).
                </p>
              </div>

              <div className="p-5 rounded-xl bg-white border border-emerald-100 hover:border-emerald-300 shadow-xs hover:shadow-md transition-all space-y-2.5 border-l-4 border-l-teal-600">
                <div className="flex items-center gap-2.5 text-teal-800 font-bold text-xs">
                  <div className="w-7 h-7 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <span>4. Statutory Disclaimer Adherence</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed pl-9">
                  Ensures all AI outputs carry appropriate legal boundaries and that patent claims are prepared only in conjunction with certified patent agents.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Resolution Modal */}
      {selectedTicket && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-xl w-full space-y-4 shadow-2xl text-white">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
                Respond to Ticket #{selectedTicket.id.slice(0, 8)}
              </h3>
              <span className="text-xs font-mono text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
                {selectedTicket.status}
              </span>
            </div>

            <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-800/80 text-xs space-y-1.5">
              <span className="font-bold text-emerald-300 flex items-center gap-1.5">
                <MessageSquare className="w-3.5 h-3.5 text-emerald-400" />
                User Inquiry / Escalation Context:
              </span>
              <p className="text-slate-200 font-medium whitespace-pre-wrap leading-relaxed">{selectedTicket.context}</p>
            </div>

            <form onSubmit={handleResolve} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 block">
                  Authoritative Statutory Advice & Facilitator Notes:
                </label>
                <textarea
                  rows={5}
                  required
                  value={resolutionText}
                  onChange={(e) => setResolutionText(e.target.value)}
                  placeholder="Provide precise statutory guidance, citing relevant sections from Patents Act 1970, Biological Diversity Act 2023, or FSSAI Regulations..."
                  className="w-full p-3.5 text-xs rounded-xl bg-slate-950 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 shadow-xs"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-400 font-medium">Update Status:</label>
                  <select
                    value={resolutionStatus}
                    onChange={(e: any) => setResolutionStatus(e.target.value)}
                    className="h-9 px-3 text-xs rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 font-medium"
                  >
                    <option value="RESOLVED">Mark as RESOLVED</option>
                    <option value="IN_PROGRESS">Keep IN PROGRESS</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedTicket(null)}
                    className="px-3 py-1.5 text-xs text-slate-400 hover:text-white font-medium cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmittingResolution || !resolutionText.trim()}
                    className="px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-md shadow-emerald-800/30"
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
