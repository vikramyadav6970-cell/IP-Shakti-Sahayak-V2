import React from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  Scale,
  ShieldAlert,
  Sparkles,
  LogIn,
  LogOut,
  User,
  ShieldCheck,
  HelpCircle,
} from "lucide-react";
import { useJurisdiction } from "@/store/useJurisdictionStore";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";
import { JurisdictionCode } from "@/types";

const INTERNATIONAL_COUNTRIES: { code: JurisdictionCode; label: string }[] = [
  { code: "USA", label: "United States (USPTO / FDA)" },
  { code: "EU", label: "European Union (EPO / EMA)" },
  { code: "UK", label: "United Kingdom (UKIPO / MHRA)" },
  { code: "JAPAN", label: "Japan (JPO / PMDA)" },
  { code: "AUSTRALIA", label: "Australia (IP Australia / TGA)" },
  { code: "WIPO", label: "WIPO / International Treaties" },
];

export const Layout: React.FC = () => {
  const { primary, internationalTarget, setPrimary, setInternationalTarget } = useJurisdiction();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50/50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white">
      {/* 1. Global Header & App Navigation */}
      <header className="sticky top-0 z-40 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Product Name */}
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center text-white shadow-md shadow-emerald-700/20 group-hover:scale-105 transition-all">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <span className="text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-1">
                IP-SAKTI
                <span className="text-emerald-700 dark:text-emerald-400 font-bold">Sahayak</span>
              </span>
              <p className="text-[10px] text-slate-600 dark:text-slate-300 font-semibold tracking-wider">
                Ministry of Ayush
              </p>
            </div>
          </Link>

          {/* Navigation Links — ONLY when logged in */}
          {isAuthenticated ? (
            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/chat"
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  location.pathname === "/chat"
                    ? "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold shadow-xs"
                    : "text-slate-600 dark:text-slate-300 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-emerald-600" />
                  Assistant
                </span>
              </Link>

              <Link
                to="/facilitator-desk"
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  location.pathname === "/facilitator-desk" || location.pathname === "/my-queries"
                    ? "bg-emerald-50 dark:bg-emerald-950/60 text-emerald-800 dark:text-emerald-300 font-semibold shadow-xs"
                    : "text-slate-600 dark:text-slate-300 hover:text-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800"
                }`}
              >
                <span className="flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-emerald-600" />
                  Facilitator Desk
                </span>
              </Link>
            </nav>
          ) : (
            <div className="hidden md:flex items-center gap-6 text-xs font-semibold text-slate-500">
              <span className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1 rounded-full border border-emerald-200 dark:border-emerald-800">
                <ShieldCheck className="w-3.5 h-3.5" />
                Verified Legal Corpus Reconciled
              </span>
            </div>
          )}

          {/* Right Side: Jurisdiction (When Logged in) & Auth Buttons */}
          <div className="flex items-center gap-3">
            {/* Jurisdiction Control — ONLY when logged in */}
            {isAuthenticated && (
              <>
                <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
                  <button
                    type="button"
                    onClick={() => setPrimary("INDIA")}
                    aria-pressed={primary === "INDIA"}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                      primary === "INDIA"
                        ? "bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-400 shadow-xs"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    🇮🇳 India
                  </button>
                  <button
                    type="button"
                    onClick={() => setPrimary("INTERNATIONAL")}
                    aria-pressed={primary === "INTERNATIONAL"}
                    className={`px-2.5 py-1 rounded text-xs font-semibold transition-all ${
                      primary === "INTERNATIONAL"
                        ? "bg-white dark:bg-slate-900 text-emerald-700 dark:text-emerald-400 shadow-xs"
                        : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                    }`}
                  >
                    🌐 International
                  </button>
                </div>

                {/* International Target Authority Dropdown */}
                {primary === "INTERNATIONAL" && (
                  <div className="hidden lg:flex items-center">
                    <select
                      value={internationalTarget}
                      onChange={(e) => setInternationalTarget(e.target.value as JurisdictionCode)}
                      aria-label="Select Target International Authority"
                      className="text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-md px-2 py-1 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                    >
                      {INTERNATIONAL_COUNTRIES.map((c) => (
                        <option key={c.code} value={c.code}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </>
            )}

            {/* Auth Buttons */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300">
                  <User className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="hidden sm:inline">{user?.name || "User"}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAuth}
                  aria-label="Log out"
                  className="h-8 px-2 text-xs text-slate-500 hover:text-destructive hover:bg-destructive/10"
                >
                  <LogOut className="w-3.5 h-3.5 mr-1" />
                  Logout
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link to="/login">
                  <Button variant="outline" size="sm" className="h-9 px-3.5 text-xs font-semibold border-slate-300 dark:border-slate-700">
                    Sign In
                  </Button>
                </Link>
                <Link to="/login">
                  <Button size="sm" className="h-9 px-4 text-xs font-semibold bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm">
                    <LogIn className="w-3.5 h-3.5 mr-1.5" />
                    Get Started
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* 2. Main Route Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>

      {/* 3. Mandatory Standing Legal Disclaimer (Moved to Bottom) */}
      <div
        role="region"
        aria-label="Standing Legal Disclaimer"
        className="bg-amber-500/10 border-t border-b border-amber-500/20 text-amber-900 dark:text-amber-200 px-4 py-2.5 text-xs md:text-sm font-medium flex items-center justify-center gap-2 text-center"
      >
        <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
        <span>
          <strong>Statutory Notice:</strong> IP-SAKTI Sahayak provides verified legal/regulatory <strong>information, not legal advice</strong>. Official filings require review by a registered patent agent or legal counsel.
        </span>
      </div>

      {/* 4. Footer */}
      <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-8 text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-emerald-700 text-white flex items-center justify-center font-bold text-xs">
              IP
            </div>
            <div>
              <p className="font-semibold text-slate-800 dark:text-slate-200">
                IP-SAKTI Sahayak — Ayush IPR & Regulatory Intelligence
              </p>
              <p className="text-[11px] text-slate-400">
                Ministry of Ayush
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-4 text-[11px]">
            <span className="text-slate-400">Primary Gazettes: WIPO Lex, IP India, NBA, FSSAI, CDSCO</span>
            <Link to="/login" className="font-semibold text-emerald-700 dark:text-emerald-400 hover:underline">
              Portal Access
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
};
