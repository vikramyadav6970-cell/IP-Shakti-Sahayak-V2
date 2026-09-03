import React, { useState } from "react";
import { ShieldCheck, LogIn, AlertCircle, Loader2, KeyRound } from "lucide-react";
import { adminService } from "../services/adminService";
import { useAdminAuthStore } from "../store/useAdminAuthStore";
import { ThemeToggle } from "./ThemeToggle";

interface AdminLoginPageProps {
  onLoginSuccess: () => void;
}

export const AdminLoginPage: React.FC<AdminLoginPageProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("admin@ayush.gov.in");
  const [password, setPassword] = useState("Admin@123");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { setAuth } = useAdminAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const tokens = await adminService.login({ email, password });
      localStorage.setItem("ip_sakti_admin_token", tokens.access_token);
      const user = await adminService.getMe();

      if (user.role !== "ADMIN") {
        throw new Error("Access restricted to System Administrators.");
      }

      setAuth(user, tokens.access_token);
      onLoginSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to authenticate administrator.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoPreview = () => {
    const mockToken = "mock-admin-token";
    localStorage.setItem("ip_sakti_admin_token", mockToken);
    setAuth(
      {
        id: "admin-preview-001",
        name: "Rajesh Verma (Admin)",
        email: "admin@ayush.gov.in",
        role: "ADMIN",
        organization: "Ministry of Ayush",
      },
      mockToken
    );
    onLoginSuccess();
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#030712] relative flex flex-col justify-center items-center p-4 selection:bg-emerald-500 selection:text-white overflow-hidden text-slate-900 dark:text-white transition-colors duration-200">
      {/* Top right ThemeToggle */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeToggle />
      </div>

      {/* Ambient background glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(16,185,129,0.12)_0%,rgba(3,13,8,0.5)_60%,transparent_90%)] pointer-events-none" />

      <div className="max-w-md w-full space-y-6 relative z-10">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-700 text-white flex items-center justify-center mx-auto shadow-xl shadow-emerald-500/25">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight flex items-center justify-center gap-1.5">
              <span>IP-SAKTI</span>
              <span className="bg-gradient-to-r from-emerald-600 to-teal-500 dark:from-emerald-400 dark:to-teal-300 bg-clip-text text-transparent drop-shadow-[0_0_20px_rgba(52,211,153,0.5)]">
                Admin Portal
              </span>
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium">
              Ministry of Ayush • Vector Corpus Management & DPDP Compliance
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-white dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200 dark:border-emerald-500/25 rounded-2xl p-6 sm:p-8 shadow-2xl shadow-emerald-950/20 dark:shadow-emerald-950/40 space-y-5 text-slate-900 dark:text-white transition-colors duration-200">
          <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300 text-xs font-medium">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <span>Administrative access for System Operators & Compliance Officers only.</span>
          </div>

          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-800/60 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2 font-medium">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Administrator Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@ayush.gov.in"
                className="w-full h-11 px-3.5 rounded-lg bg-slate-50 dark:bg-slate-950/80 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white text-xs placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full h-11 px-3.5 rounded-lg bg-slate-50 dark:bg-slate-950/80 border border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white text-xs placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-11 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-semibold text-xs transition-all flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.35)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] disabled:opacity-50 cursor-pointer"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              Sign In to Admin Portal
            </button>

            <button
              type="button"
              onClick={handleDemoPreview}
              className="w-full h-10 rounded-lg bg-slate-100 dark:bg-slate-800/80 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-700/80 text-slate-700 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-300 font-semibold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Explore as System Admin (Instant Preview)</span>
            </button>
          </form>

          {/* Seed Credentials Hint */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 text-[11px] text-slate-600 space-y-1.5">
            <div className="flex items-center gap-1.5 text-emerald-700 font-semibold">
              <KeyRound className="w-3.5 h-3.5 text-emerald-600" />
              <span>Default Credentials (Pre-filled):</span>
            </div>
            <div className="font-mono text-[10px] space-y-0.5 text-slate-500">
              <div>Email: <span className="text-slate-800 font-medium">admin@ayush.gov.in</span></div>
              <div>Password: <span className="text-slate-800 font-medium">Admin@123</span></div>
            </div>
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-500">
          DPDP-compliant immutable access management and vector corpus operations.
        </p>
      </div>
    </div>
  );
};
