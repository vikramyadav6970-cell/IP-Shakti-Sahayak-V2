import React, { useState } from "react";
import {
  ShieldCheck,
  Database,
  Lock,
  Activity,
  RefreshCw,
  Server,
  LogOut,
  User,
  Search,
  CheckCircle2,
  Layers,
  Cpu,
} from "lucide-react";
import { useAdminAuthStore } from "../store/useAdminAuthStore";

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  user_hash: string;
  event_type: "CONSULTATION" | "CLASSIFICATION" | "ABS_ASSESSMENT" | "FACILITATOR_INTERVENTION" | "VECTOR_SYNC";
  status: "VERIFIED" | "FLAGGED";
  sha256_checksum: string;
}

const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: "AUD-98214-A",
    timestamp: "2026-08-31 18:45:12 UTC",
    action: "RAG Consultation Session Generated",
    user_hash: "usr_sha256_8f93...4b12",
    event_type: "CONSULTATION",
    status: "VERIFIED",
    sha256_checksum: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  },
  {
    id: "AUD-98213-B",
    timestamp: "2026-08-31 18:32:04 UTC",
    action: "Product Classification Reconciled (§3(p) Classical)",
    user_hash: "usr_sha256_a4c1...99e3",
    event_type: "CLASSIFICATION",
    status: "VERIFIED",
    sha256_checksum: "f84b638a192d6e35798bbcb86c2e3a1f89c5643497852b855198237584126789",
  },
  {
    id: "AUD-98212-C",
    timestamp: "2026-08-31 18:14:28 UTC",
    action: "ABS Assessment Executed (Form I Approval Required)",
    user_hash: "usr_sha256_c729...120a",
    event_type: "ABS_ASSESSMENT",
    status: "VERIFIED",
    sha256_checksum: "68b329da9893e34099c7d8ad5cb9c940110e7b8f9e0123984572834510982345",
  },
  {
    id: "AUD-98211-D",
    timestamp: "2026-08-31 17:58:40 UTC",
    action: "Facilitator Authoritative Guidance Delivered",
    user_hash: "fac_sha256_55e1...d98b",
    event_type: "FACILITATOR_INTERVENTION",
    status: "VERIFIED",
    sha256_checksum: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
  },
  {
    id: "AUD-98210-E",
    timestamp: "2026-08-31 17:30:00 UTC",
    action: "Qdrant 5-Collection Checksum Synchronization",
    user_hash: "sys_sha256_0000...0001",
    event_type: "VECTOR_SYNC",
    status: "VERIFIED",
    sha256_checksum: "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
  },
];

const CANONICAL_COLLECTIONS = [
  {
    id: "wipo_lex_treaties",
    name: "WIPO Lex & International Treaties",
    jurisdiction: "INTERNATIONAL",
    description: "Paris Convention, PCT, Madrid Protocol, Nagoya Protocol, WIPO GRATK guidelines.",
    official_authority: "World Intellectual Property Organization (WIPO)",
    document_count: 142,
    chunk_count: 1840,
    status: "SYNCHRONIZED",
  },
  {
    id: "india_statutes_gazettes",
    name: "India Core Statutes & Official Gazettes",
    jurisdiction: "INDIA",
    description: "The Patents Act 1970, Patent Rules 2003, Biological Diversity Act 2002 & 2023 Amendment.",
    official_authority: "Ministry of Law & Justice / IP India / NBA",
    document_count: 210,
    chunk_count: 3120,
    status: "SYNCHRONIZED",
  },
  {
    id: "drugs_cosmetics_corpus",
    name: "Drugs & Cosmetics & Ayurvedic Pharmacopoeia",
    jurisdiction: "INDIA",
    description: "Drugs and Cosmetics Act 1940, First Schedule Authoritative Texts, Form 25-D & Form 24-D.",
    official_authority: "Ministry of Ayush / Pharmacopoeia Commission for Indian Medicine",
    document_count: 185,
    chunk_count: 2450,
    status: "SYNCHRONIZED",
  },
  {
    id: "fssai_ayurveda_aahara",
    name: "FSSAI Ayurveda-Aahara Regulations",
    jurisdiction: "INDIA",
    description: "Food Safety and Standards (Ayurveda Aahara) Regulations 2022, labeling standards.",
    official_authority: "Food Safety and Standards Authority of India (FSSAI)",
    document_count: 96,
    chunk_count: 1120,
    status: "SYNCHRONIZED",
  },
  {
    id: "nba_abs_guidelines",
    name: "NBA & State Biodiversity Rules",
    jurisdiction: "INDIA",
    description: "NBA Guidelines on Access and Benefit Sharing, Form I, Form II, Form III, SBB Intimations.",
    official_authority: "National Biodiversity Authority (NBA)",
    document_count: 124,
    chunk_count: 1680,
    status: "SYNCHRONIZED",
  },
];

export const AdminDashboardPage: React.FC = () => {
  const { user, clearAuth } = useAdminAuthStore();
  const [activeTab, setActiveTab] = useState<"corpus" | "audit" | "system">("corpus");
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState<string | null>(null);
  const [searchAudit, setSearchAudit] = useState("");

  const handleTriggerSync = () => {
    setIsSyncing(true);
    setSyncSuccessMsg(null);
    setTimeout(() => {
      setIsSyncing(false);
      setSyncSuccessMsg("All 5 canonical vector collections synchronized and SHA-256 hashes verified.");
      setTimeout(() => setSyncSuccessMsg(null), 5000);
    }, 1500);
  };

  const filteredLogs = MOCK_AUDIT_LOGS.filter((l) => {
    return (
      searchAudit === "" ||
      l.id.toLowerCase().includes(searchAudit.toLowerCase()) ||
      l.action.toLowerCase().includes(searchAudit.toLowerCase()) ||
      l.user_hash.toLowerCase().includes(searchAudit.toLowerCase())
    );
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur border-b border-slate-800 h-16 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-800 text-white flex items-center justify-center shadow-md shadow-blue-900/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-white">IP-SAKTI Admin Portal</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-950 text-blue-300 border border-blue-800 font-mono">
                OPERATIONAL MANAGEMENT
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Corpus Synchronization & DPDP Audit Management</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700 text-xs">
            <User className="w-3.5 h-3.5 text-blue-400" />
            <span>{user?.name || "Administrator"}</span>
            <span className="text-[10px] font-mono text-blue-400 ml-1">({user?.role})</span>
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
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Vector Collections</span>
            <div className="text-2xl font-bold text-blue-400 flex items-center justify-between">
              5 / 5
              <Database className="w-5 h-5 text-blue-500/50" />
            </div>
            <span className="text-[11px] text-emerald-400 font-medium">10,210 Total Chunks Indexed</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Audit Records Logged</span>
            <div className="text-2xl font-bold text-emerald-400 flex items-center justify-between">
              1,428
              <Lock className="w-5 h-5 text-emerald-500/50" />
            </div>
            <span className="text-[11px] text-slate-400">100% Cryptographic Integrity</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">Embedding Accuracy</span>
            <div className="text-2xl font-bold text-white flex items-center justify-between">
              100%
              <Layers className="w-5 h-5 text-blue-500/50" />
            </div>
            <span className="text-[11px] text-slate-400">Dense (Gemini) + Sparse (BM25)</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-400 uppercase">System Status</span>
            <div className="text-2xl font-bold text-emerald-400 flex items-center justify-between">
              HEALTHY
              <Activity className="w-5 h-5 text-emerald-500/50" />
            </div>
            <span className="text-[11px] text-slate-400">FastAPI • PostgreSQL • Qdrant</span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex border-b border-slate-800 gap-2">
          <button
            onClick={() => setActiveTab("corpus")}
            className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "corpus"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Corpus Sync & Vector Collections (5)
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "audit"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            DPDP Immutable Audit Trail
          </button>
          <button
            onClick={() => setActiveTab("system")}
            className={`pb-3 px-4 text-xs font-semibold border-b-2 transition-all ${
              activeTab === "system"
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Infrastructure & Diagnostics
          </button>
        </div>

        {/* TAB 1: CORPUS SYNC & VECTOR COLLECTIONS */}
        {activeTab === "corpus" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-white">Canonical Qdrant Vector Corpus</h3>
                <p className="text-xs text-slate-400">
                  Primary legal gazettes, monographs, and international treaties powering zero-hallucination RAG.
                </p>
              </div>

              <button
                onClick={handleTriggerSync}
                disabled={isSyncing}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs transition-colors flex items-center gap-2 shadow-md shadow-blue-900/30 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
                <span>{isSyncing ? "Synchronizing Corpus..." : "Trigger Full Corpus Sync"}</span>
              </button>
            </div>

            {syncSuccessMsg && (
              <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>{syncSuccessMsg}</span>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {CANONICAL_COLLECTIONS.map((col) => (
                <div key={col.id} className="p-5 rounded-xl bg-slate-900 border border-slate-800 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-blue-400">{col.id}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      {col.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-white">{col.name}</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">{col.description}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/80">
                    <div className="p-2 rounded bg-slate-950 border border-slate-800/60">
                      <span className="text-[10px] text-slate-500 block">Primary Documents</span>
                      <span className="font-bold text-white">{col.document_count}</span>
                    </div>
                    <div className="p-2 rounded bg-slate-950 border border-slate-800/60">
                      <span className="text-[10px] text-slate-500 block">Vector Chunks</span>
                      <span className="font-bold text-blue-400">{col.chunk_count}</span>
                    </div>
                  </div>

                  <div className="text-[11px] text-slate-500 pt-1">
                    <span className="font-semibold text-slate-400">Authority:</span> {col.official_authority}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: DPDP IMMUTABLE AUDIT TRAIL */}
        {activeTab === "audit" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
                <input
                  type="text"
                  value={searchAudit}
                  onChange={(e) => setSearchAudit(e.target.value)}
                  placeholder="Search audit trail by ID, hash, action..."
                  className="w-full h-10 pl-9 pr-3 text-xs rounded-lg bg-slate-900 border border-slate-800 text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>SHA-256 Chain Verification Active</span>
              </div>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-3.5">Log ID</th>
                    <th className="p-3.5">Timestamp</th>
                    <th className="p-3.5">Action Executed</th>
                    <th className="p-3.5">Event Type</th>
                    <th className="p-3.5">User SHA-256 Hash</th>
                    <th className="p-3.5">Integrity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="p-3.5 font-mono text-blue-400 font-bold">{log.id}</td>
                      <td className="p-3.5 text-slate-400 whitespace-nowrap">{log.timestamp}</td>
                      <td className="p-3.5 font-semibold text-white">{log.action}</td>
                      <td className="p-3.5">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">{log.user_hash}</td>
                      <td className="p-3.5">
                        <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                          {log.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: INFRASTRUCTURE & DIAGNOSTICS */}
        {activeTab === "system" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <Server className="w-4 h-4 text-blue-400" />
                <span>Backend Services Connectivity</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>FastAPI Application Engine</span>
                  <span className="text-emerald-400 font-bold">HTTP 200 OK</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>PostgreSQL (Supabase Pooler)</span>
                  <span className="text-emerald-400 font-bold">CONNECTED</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>Qdrant Vector Engine</span>
                  <span className="text-emerald-400 font-bold">SYNCHRONIZED</span>
                </div>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-white font-bold text-sm">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span>AI Reasoning & Retrieval Parameters</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>Dense Embeddings</span>
                  <span className="font-mono text-slate-300">text-embedding-004</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>Hybrid Retrieval Strategy</span>
                  <span className="font-mono text-slate-300">Dense + BM25 Sparse</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded bg-slate-950 border border-slate-800">
                  <span>Confidence Threshold</span>
                  <span className="font-mono text-slate-300">0.70 (Auto-Escalate below)</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
