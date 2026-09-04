import React, { useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import {
  ShieldAlert,
  Sparkles,
  LogIn,
  LogOut,
  User,
  HelpCircle,
  Plug,
  ChevronDown,
  ChevronUp,
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
  const [isNoticeExpanded, setIsNoticeExpanded] = useState(false);
  const location = useLocation();
  const isChatPage = location.pathname === "/chat";
  const isLandingPage = location.pathname === "/" || location.pathname === "";

  return (
    <div className={`min-h-screen flex flex-col bg-slate-50 dark:bg-[#030712] font-sans text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white ${isChatPage ? "h-screen overflow-hidden" : ""}`}>
      {/* 1. Global Header & App Navigation */}
      {isLandingPage ? (
        /* Completely Transparent Floating Header on Landing Page (Tree 100% Visible) */
        <header className="sticky top-0 z-40 w-full px-4 sm:px-8 max-w-7xl mx-auto py-4 sm:py-5 flex items-center justify-between gap-4 bg-transparent border-none shadow-none transition-all duration-300">
          {/* Logo & Product Name */}
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <div className="relative w-11 h-11 rounded-2xl p-[1.5px] bg-gradient-to-br from-amber-400 via-emerald-400 to-teal-500 shadow-[0_0_20px_rgba(16,185,129,0.4)] group-hover:shadow-[0_0_30px_rgba(16,185,129,0.6)] group-hover:scale-105 transition-all duration-300 shrink-0">
              <div className="w-full h-full rounded-[14px] overflow-hidden bg-slate-950 p-1.5 flex items-center justify-center">
                <img
                  src="/ayush-logo.svg"
                  alt="Ministry of Ayush - IP-SAKTI Sahayak Emblem"
                  className="w-full h-full object-contain select-none"
                />
              </div>
            </div>
            <div>
              <span className="font-display text-base font-bold tracking-tight text-white flex items-center gap-1">
                IP-SAKTI
                <span className="text-emerald-400 font-bold">Sahayak</span>
              </span>
              <p className="text-[10px] text-slate-400 font-medium tracking-wider">
                Ministry of Ayush
              </p>
            </div>
          </Link>

          {/* Navigation Links (Only accessible when logged in) */}
          {isAuthenticated && (
            <nav className="hidden md:flex items-center gap-2">
              <Link
                to="/chat"
                className="px-4 py-2 rounded-full text-xs font-semibold bg-slate-900/40 hover:bg-slate-900/70 text-slate-200 hover:text-emerald-300 border border-white/10 hover:border-emerald-400/40 backdrop-blur-md transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-lg"
              >
                <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                <span>AI Assistant</span>
              </Link>

              <Link
                to="/facilitator-desk"
                className="px-4 py-2 rounded-full text-xs font-semibold bg-slate-900/40 hover:bg-slate-900/70 text-slate-200 hover:text-emerald-300 border border-white/10 hover:border-emerald-400/40 backdrop-blur-md transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-lg"
              >
                <HelpCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span>Facilitator Desk</span>
              </Link>

              <Link
                to="/connections"
                className="px-4 py-2 rounded-full text-xs font-semibold bg-slate-900/40 hover:bg-slate-900/70 text-slate-200 hover:text-emerald-300 border border-white/10 hover:border-emerald-400/40 backdrop-blur-md transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-lg"
              >
                <Plug className="w-3.5 h-3.5 text-emerald-400" />
                <span>Integrations</span>
              </Link>
            </nav>
          )}

          {/* Right Side: Auth Buttons (Separate Floating Pills with Dynamic Fill Hover) */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-2.5">
                <Link
                  to="/login"
                  title="View Account / Switch Profile"
                  className="h-10 px-4 rounded-full bg-slate-900/40 hover:bg-slate-900/70 border border-white/15 hover:border-emerald-400/40 text-xs font-semibold text-slate-200 hover:text-white transition-all duration-300 cursor-pointer backdrop-blur-md flex items-center gap-2 shadow-lg hover:scale-105"
                >
                  <User className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden sm:inline">{user?.name || "User"}</span>
                </Link>
                <button
                  type="button"
                  onClick={clearAuth}
                  aria-label="Log out"
                  className="h-10 px-4 text-xs font-semibold text-slate-300 hover:text-destructive bg-slate-900/40 hover:bg-destructive/15 border border-white/10 hover:border-destructive/30 rounded-full cursor-pointer transition-all duration-300 backdrop-blur-md flex items-center gap-1.5 shadow-lg hover:scale-105 active:scale-95"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3.5">
                {/* Sign In - Sleek Rectangular with Smooth Glow on Hover */}
                <Link to="/login" className="group relative inline-flex items-center justify-center">
                  <button
                    type="button"
                    className="relative overflow-hidden h-11 min-w-[105px] px-7 rounded-xl text-sm font-semibold tracking-wide text-slate-200 group-hover:text-white bg-slate-950/70 backdrop-blur-xl border border-emerald-500/35 group-hover:border-emerald-400/80 shadow-lg transition-all duration-300 cursor-pointer flex items-center justify-center group-hover:-translate-y-0.5 active:translate-y-0"
                  >
                    {/* Smooth hover glow */}
                    <span className="absolute inset-0 bg-gradient-to-r from-emerald-700/80 to-teal-700/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                    
                    {/* Foreground text */}
                    <span className="relative z-10 flex items-center justify-center gap-2 whitespace-nowrap">
                      <span>Sign In</span>
                    </span>
                  </button>
                </Link>

                {/* Sign Up - Sleek Rectangular with Smooth Radiant Glow */}
                <Link to="/login" className="group relative inline-flex items-center justify-center">
                  <button
                    type="button"
                    className="relative overflow-hidden h-11 min-w-[115px] px-7.5 rounded-xl text-sm font-bold tracking-wide text-white bg-emerald-950/90 backdrop-blur-xl border border-emerald-400/50 shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] transition-all duration-300 cursor-pointer flex items-center justify-center group-hover:-translate-y-0.5 active:translate-y-0"
                  >
                    {/* Smooth glowing emerald fill */}
                    <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                    
                    {/* Foreground text & icon */}
                    <span className="relative z-10 flex items-center justify-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
                      <LogIn className="w-4 h-4 shrink-0 group-hover:translate-x-0.5 transition-transform duration-300" />
                      <span>Sign Up</span>
                    </span>
                  </button>
                </Link>
              </div>
            )}
          </div>
        </header>
      ) : (
        /* Standard Header on Internal Pages */
        <header className="sticky top-0 z-40 bg-white/90 dark:bg-[#030712]/85 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 shadow-xs">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
            {/* Logo & Product Name */}
            <Link to="/" className="flex items-center gap-3 group shrink-0">
              <div className="relative w-10 h-10 rounded-xl p-[1.5px] bg-gradient-to-br from-amber-400 via-emerald-400 to-teal-500 shadow-md shadow-emerald-700/20 group-hover:scale-105 transition-all shrink-0">
                <div className="w-full h-full rounded-[10px] overflow-hidden bg-slate-950 p-1 flex items-center justify-center">
                  <img
                    src="/ayush-logo.svg"
                    alt="Ministry of Ayush - IP-SAKTI Sahayak Emblem"
                    className="w-full h-full object-contain select-none"
                  />
                </div>
              </div>
              <div>
                <span className="font-display text-base font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-1">
                  IP-SAKTI
                  <span className="text-emerald-700 dark:text-emerald-400 font-bold">Sahayak</span>
                </span>
                <p className="text-[10px] text-slate-600 dark:text-slate-300 font-semibold tracking-wider">
                  Ministry of Ayush
                </p>
              </div>
            </Link>

            {/* Navigation Links */}
            {isAuthenticated && (
              <nav className="hidden md:flex items-center gap-2">
                <Link
                  to="/chat"
                  className={`group relative overflow-hidden px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold border transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-xs ${
                    location.pathname === "/chat"
                      ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-emerald-500 shadow-emerald-950/30 font-bold"
                      : "bg-slate-100/90 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-50/50 dark:hover:bg-slate-800"
                  }`}
                >
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
                  <HelpCircle className={`w-3.5 h-3.5 relative z-10 ${location.pathname === "/facilitator-desk" || location.pathname === "/my-queries" ? "text-amber-300" : "text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform duration-300"}`} />
                  <span className="relative z-10">Facilitator Desk</span>
                </Link>

                <Link
                  to="/connections"
                  className={`group relative overflow-hidden px-3.5 py-1.5 rounded-xl text-xs sm:text-sm font-semibold border transition-all duration-300 flex items-center gap-1.5 cursor-pointer shadow-xs ${
                    location.pathname === "/connections"
                      ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-emerald-500 shadow-emerald-950/30 font-bold"
                      : "bg-slate-100/90 dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:text-emerald-700 dark:hover:text-emerald-300 hover:border-emerald-400/50 hover:bg-emerald-50/50 dark:hover:bg-slate-800"
                  }`}
                >
                  <Plug className={`w-3.5 h-3.5 relative z-10 ${location.pathname === "/connections" ? "text-amber-300" : "text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform duration-300"}`} />
                  <span className="relative z-10">Integrations</span>
                </Link>
              </nav>
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
                  <Link
                    to="/login"
                    title="View Account / Switch Profile"
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
                  >
                    <User className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span className="hidden sm:inline">{user?.name || "User"}</span>
                  </Link>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAuth}
                    aria-label="Log out"
                    className="h-8 px-2 text-xs text-slate-500 hover:text-destructive hover:bg-destructive/10 cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5 mr-1" />
                    Logout
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link to="/login">
                    <Button variant="outline" size="sm" className="h-9 px-3.5 text-xs font-semibold rounded-lg border-slate-300 dark:border-slate-700">
                      Sign In
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button size="sm" className="h-9 px-4 text-xs font-semibold rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white shadow-sm">
                      <LogIn className="w-3.5 h-3.5 mr-1.5" />
                      Sign Up
                    </Button>
                  </Link>
                </div>
              )}

              {/* Theme Toggle (Dark / Bright mode) — on each page except landing page */}
              {!isLandingPage && <ThemeToggle />}
            </div>
          </div>
        </header>
      )}

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

      {/* 3. Sleek Expandable Statutory Legal Notice & Footer (Hidden on Chat) */}
      {!isChatPage && (
        <>
          {/* Expandable Statutory Notice Button & Glass Accordion */}
          <section className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-4 flex flex-col items-center justify-center">
            <button
              type="button"
              onClick={() => setIsNoticeExpanded((prev) => !prev)}
              aria-expanded={isNoticeExpanded}
              className="group relative flex items-center gap-2.5 px-5 py-2.5 rounded-xl bg-slate-900/50 hover:bg-slate-900/80 border border-emerald-500/20 hover:border-emerald-400/50 backdrop-blur-xl text-xs font-medium text-slate-300 hover:text-white transition-all duration-300 cursor-pointer shadow-lg hover:shadow-[0_0_25px_rgba(16,185,129,0.2)]"
            >
              <ShieldAlert className="w-3.5 h-3.5 text-emerald-400 group-hover:scale-110 transition-transform duration-300" />
              <span className="tracking-wide">Statutory Legal Disclaimer & Regulatory Advisory</span>
              <span className="p-0.5 rounded-md bg-white/5 border border-white/10 text-slate-400 group-hover:text-emerald-300 transition-colors">
                {isNoticeExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </span>
            </button>

            {/* Expandable Frosted Glass Content Panel */}
            {isNoticeExpanded && (
              <div className="mt-3 w-full p-4 sm:p-5 rounded-2xl bg-gradient-to-b from-slate-950/95 via-[#021812]/95 to-slate-950/95 backdrop-blur-2xl border border-emerald-500/30 text-slate-300 text-xs leading-relaxed shadow-2xl animate-in fade-in zoom-in-95 duration-300">
                <div className="flex items-start gap-3.5">
                  <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 shrink-0 mt-0.5">
                    <ShieldAlert className="w-4 h-4" />
                  </div>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-white tracking-wide font-display text-sm">
                        Statutory Legal Disclaimer · Non-Legal Advice Notice
                      </p>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 text-[10px] font-bold">
                        Official Gazette Compliance
                      </span>
                    </div>
                    <p className="text-slate-300 font-normal leading-relaxed">
                      IP-SAKTI Sahayak provides verified legal intelligence and statutory reference mapping grounded in published Indian and international gazettes (Patents Act 1970, Biodiversity Act 2002, Drugs & Cosmetics Act 1940, WIPO Lex). This platform does <strong className="text-emerald-300 font-semibold underline underline-offset-2">not constitute formal legal counsel</strong>. Official commercial submissions and filings must be verified by a registered patent agent or certified legal practitioner.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </section>

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
                <Link to={isAuthenticated ? "/chat" : "/login"} className="text-white hover:text-emerald-300 transition-colors font-bold underline underline-offset-2" style={{ color: "#ffffff" }}>
                  {isAuthenticated ? "Consultation Portal" : "Portal Access"}
                </Link>
              </div>
            </div>
          </footer>
        </>
      )}
    </div>
  );
};
