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
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";

export const Layout: React.FC = () => {
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const location = useLocation();
  const isChatPage = location.pathname === "/chat" || location.pathname.startsWith("/chat");

  return (
    <div
      className={`${
        isChatPage ? "h-screen overflow-hidden" : "min-h-screen"
      } flex flex-col bg-slate-50/50 dark:bg-slate-950 font-sans text-slate-900 dark:text-slate-100 selection:bg-emerald-500 selection:text-white`}
    >
      {/* 1. Global Header & App Navigation */}
      <header className="sticky top-0 z-40 shrink-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 shadow-xs">
        <div
          className={`${
            isChatPage ? "w-full px-3 sm:px-5" : "max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
          } h-14 sm:h-16 flex items-center justify-between gap-4`}
        >
          {/* Logo & Product Name */}
          <Link to="/" className="flex items-center gap-3 group shrink-0">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center text-white shadow-md shadow-emerald-700/20 group-hover:scale-105 transition-all">
              <Scale className="w-4 h-4 sm:w-5 sm:h-5" />
            </div>
            <div>
              <span className="text-sm sm:text-base font-black tracking-tight text-slate-900 dark:text-white flex items-center gap-1">
                IP-SAKTI
                <span className="text-emerald-700 dark:text-emerald-400 font-bold">Sahayak</span>
              </span>
              <p className="text-[9px] sm:text-[10px] text-slate-600 dark:text-slate-300 font-semibold tracking-wider">
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
            {/* User Profile & Logout */}
            {isAuthenticated ? (
              <div className="flex items-center gap-2">
                <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs">
                  <User className="w-3.5 h-3.5 text-slate-500" />
                  <span className="font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[120px]">
                    {user?.name || user?.email?.split("@")[0]}
                  </span>
                  <span className="text-[10px] bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300 px-1.5 py-0.2 rounded font-bold uppercase">
                    {user?.role || "INNOVATOR"}
                  </span>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAuth}
                  className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/50 gap-1 h-8"
                  title="Logout"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </Button>
              </div>
            ) : (
              <Link to="/login">
                <Button size="sm" className="text-xs bg-emerald-700 hover:bg-emerald-800 text-white gap-1.5 h-8">
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Portal Login</span>
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* 2. Main Route Body */}
      <main
        className={`flex-1 w-full ${
          isChatPage
            ? "max-w-none px-2 sm:px-4 py-2 overflow-hidden flex flex-col min-h-0"
            : "max-w-7xl mx-auto p-4 sm:p-6 lg:p-8"
        }`}
      >
        <Outlet />
      </main>

      {/* 3. Non-Chat Standing Legal Disclaimer & Footer */}
      {!isChatPage && (
        <>
          <div
            role="region"
            aria-label="Standing Legal Disclaimer"
            className="bg-amber-500/10 border-t border-b border-amber-500/20 text-amber-900 dark:text-amber-200 px-4 py-2.5 text-xs md:text-sm font-medium flex items-center justify-center gap-2 text-center shrink-0"
          >
            <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>
              <strong>Statutory Notice:</strong> IP-SAKTI Sahayak provides verified legal/regulatory <strong>information, not legal advice</strong>. Official filings require review by a registered patent agent or legal counsel.
            </span>
          </div>

          <footer className="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-8 text-xs text-slate-500 dark:text-slate-400 shrink-0">
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
        </>
      )}
    </div>
  );
};
