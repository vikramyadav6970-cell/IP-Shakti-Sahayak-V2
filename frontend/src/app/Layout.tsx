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
import { ThemeToggle } from "@/components/common/ThemeToggle";

interface InternationalCountry {
  code: JurisdictionCode;
  label: string;
}

const INTERNATIONAL_COUNTRIES: InternationalCountry[] = [
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
  const isChatPage = location.pathname === "/chat";
  const isLandingPage = location.pathname === "/" || location.pathname === "";

  return (
    <div className={`min-h-screen flex flex-col bg-slate-50 dark:bg-[#030712] font-sans text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white ${isChatPage ? "h-screen overflow-hidden" : ""}`}>
      {/* 1. Global Header & App Navigation */}
      <header className="sticky top-0 z-40 bg-white/90 dark:bg-[#030712]/85 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 shadow-xs">
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
            <nav className="hidden md:flex items-center gap-2">
              <Link
                to="/chat"
                className={`group relative overflow-hidden px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold border transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-xs ${
                  location.pathname === "/chat"
                    ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-emerald-500 shadow-emerald-950/30 font-bold"
                    : "bg-slate-100/90 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-50/50 dark:hover:bg-slate-800"
                }`}
              >
                {/* Radial fluid fill on hover */}
                {location.pathname !== "/chat" && (
                  <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400/20 via-emerald-500/25 to-teal-500/20 group-hover:w-[220px] group-hover:h-[220px] transition-all duration-500 ease-out pointer-events-none" />
                )}
                <Sparkles className={`w-3.5 h-3.5 relative z-10 ${location.pathname === "/chat" ? "text-amber-300 animate-pulse" : "text-emerald-600 dark:text-emerald-400 group-hover:rotate-12 transition-transform duration-300"}`} />
                <span className="relative z-10">AI Assistant</span>
              </Link>

              <Link
                to="/facilitator-desk"
                className={`group relative overflow-hidden px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold border transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-xs ${
                  location.pathname === "/facilitator-desk" || location.pathname === "/my-queries"
                    ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-emerald-500 shadow-emerald-950/30 font-bold"
                    : "bg-slate-100/90 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-50/50 dark:hover:bg-slate-800"
                }`}
              >
                {/* Radial fluid fill on hover */}
                {!(location.pathname === "/facilitator-desk" || location.pathname === "/my-queries") && (
                  <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400/20 via-emerald-500/25 to-teal-500/20 group-hover:w-[240px] group-hover:h-[240px] transition-all duration-500 ease-out pointer-events-none" />
                )}
                <HelpCircle className={`w-3.5 h-3.5 relative z-10 ${location.pathname === "/facilitator-desk" || location.pathname === "/my-queries" ? "text-amber-300" : "text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform duration-300"}`} />
                <span className="relative z-10">Facilitator Desk</span>
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

            {/* Theme Toggle (Dark / Bright mode) — on each page except landing page */}
            {!isLandingPage && <ThemeToggle />}
          </div>
        </div>
      </header>

      {/* 2. Main Route Body */}
      <main
        className={`flex-1 w-full mx-auto relative z-10 ${
          isChatPage
            ? "h-[calc(100vh-64px)] p-2 sm:p-3 overflow-hidden min-h-0 max-w-[1600px]"
            : "max-w-7xl p-4 sm:p-6 lg:p-8"
        }`}
      >
        <Outlet />
      </main>

      {/* 3. Mandatory Standing Legal Disclaimer & Footer (Hidden on Chat to ensure ChatGPT/Gemini single-window fixed layout) */}
      {!isChatPage && (
        <>
          <div
            role="region"
            aria-label="Standing Legal Disclaimer"
            className="relative z-10 bg-amber-950/90 border-t border-b border-amber-500/50 text-white px-4 py-3 text-xs md:text-sm font-medium flex items-center justify-center gap-2 text-center shadow-md backdrop-blur-md"
            style={{ color: "#ffffff" }}
          >
            <ShieldAlert className="w-4 h-4 text-amber-300 shrink-0" />
            <span className="text-white" style={{ color: "#ffffff" }}>
              <strong className="text-amber-300 font-bold">Statutory Notice:</strong> IP-SAKTI Sahayak provides verified legal/regulatory <strong className="underline decoration-amber-400">information, not legal advice</strong>. Official filings require review by a registered patent agent or legal counsel.
            </span>
          </div>

          {/* 4. Static Legal Footer with Direct Links */}
          <footer className="relative z-10 bg-slate-950 border-t border-slate-800 py-8 text-xs text-white shadow-2xl" style={{ color: "#ffffff" }}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-5 text-white">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 text-white flex items-center justify-center font-extrabold text-sm shadow-md shadow-emerald-900/40 border border-emerald-400/30">
                  IP
                </div>
                <div>
                  <p className="font-bold text-white text-sm tracking-tight" style={{ color: "#ffffff" }}>
                    IP-SAKTI Sahayak — Ayush IPR & Regulatory Intelligence
                  </p>
                  <p className="text-xs text-white font-medium" style={{ color: "#ffffff" }}>
                    Ministry of Ayush · Government of India
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs text-white">
                <span className="text-white flex items-center gap-1.5 font-medium flex-wrap" style={{ color: "#ffffff" }}>
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="font-bold text-white" style={{ color: "#ffffff" }}>Primary Gazettes:</span>
                  <a href="https://wipolex.wipo.int/" target="_blank" rel="noopener noreferrer" className="text-white hover:text-emerald-300 font-semibold underline underline-offset-2 transition-colors" style={{ color: "#ffffff" }}>WIPO Lex</a>,
                  <a href="https://ipindia.gov.in/" target="_blank" rel="noopener noreferrer" className="text-white hover:text-emerald-300 font-semibold underline underline-offset-2 transition-colors" style={{ color: "#ffffff" }}>IP India</a>,
                  <a href="http://nbaindia.org/" target="_blank" rel="noopener noreferrer" className="text-white hover:text-emerald-300 font-semibold underline underline-offset-2 transition-colors" style={{ color: "#ffffff" }}>NBA</a>,
                  <a href="https://www.fssai.gov.in/" target="_blank" rel="noopener noreferrer" className="text-white hover:text-emerald-300 font-semibold underline underline-offset-2 transition-colors" style={{ color: "#ffffff" }}>FSSAI</a>,
                  <a href="https://cdsco.gov.in/" target="_blank" rel="noopener noreferrer" className="text-white hover:text-emerald-300 font-semibold underline underline-offset-2 transition-colors" style={{ color: "#ffffff" }}>CDSCO</a>
                </span>
                <span className="text-white font-bold hidden sm:inline" style={{ color: "#ffffff" }}>•</span>
                <Link to="/sources" className="text-white hover:text-emerald-300 transition-colors font-bold underline underline-offset-2" style={{ color: "#ffffff" }}>
                  Legal Sources
                </Link>
                <span className="text-white font-bold hidden sm:inline" style={{ color: "#ffffff" }}>•</span>
                <Link to="/login" className="text-white hover:text-emerald-300 transition-colors font-bold underline underline-offset-2" style={{ color: "#ffffff" }}>
                  Portal Access
                </Link>
              </div>
            </div>
          </footer>
        </>
      )}
    </div>
  );
};
