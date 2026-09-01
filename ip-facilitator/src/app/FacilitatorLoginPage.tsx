import React, { useState } from "react";
import { Scale, LogIn, AlertCircle, Loader2, ShieldCheck, KeyRound } from "lucide-react";
import { facilitatorService } from "../services/facilitatorService";
import { useFacilitatorAuthStore } from "../store/useFacilitatorAuthStore";

interface FacilitatorLoginPageProps {
  onLoginSuccess: () => void;
}

export const FacilitatorLoginPage: React.FC<FacilitatorLoginPageProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("facilitator@ayush.gov.in");
  const [password, setPassword] = useState("Facilitator@123");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { setAuth } = useFacilitatorAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const tokens = await facilitatorService.login({ email, password });
      localStorage.setItem("ip_sakti_facilitator_token", tokens.access_token);
      const user = await facilitatorService.getMe();

      if (user.role !== "ADMIN" && user.role !== "IP_FACILITATOR" && user.role !== "CONTENT_MANAGER") {
        throw new Error("Access restricted to assigned IP Facilitators.");
      }

      setAuth(user, tokens.access_token);
      onLoginSuccess();
    } catch (err: any) {
      setErrorMessage(err.message || "Authentication failed. Invalid facilitator credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
      <div className="max-w-md w-full space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-600 to-teal-800 text-white flex items-center justify-center mx-auto shadow-xl shadow-emerald-900/30">
            <Scale className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              IP Facilitator Portal
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Ministry of Ayush • Institutional Decision & Escalation Support
            </p>
          </div>
        </div>

        {/* Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-5">
          <div className="flex items-center gap-2 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/40 text-emerald-300 text-xs">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>Authorized access for verified IP Facilitators & Legal Specialists only.</span>
          </div>

          {errorMessage && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/40 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Official Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="facilitator@ayush.gov.in"
                className="w-full h-11 px-3.5 rounded-lg bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Password
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full h-11 px-3.5 rounded-lg bg-slate-800 border border-slate-700 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full h-11 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/40 disabled:opacity-50"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              Sign In to Facilitation Desk
            </button>
          </form>

          {/* Seed Credentials Hint */}
          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
              <KeyRound className="w-3.5 h-3.5" />
              <span>Seeded Facilitator Credentials</span>
            </div>
            <p>Email: <code className="text-slate-200">facilitator@ayush.gov.in</code></p>
            <p>Password: <code className="text-slate-200">Facilitator@123</code></p>
          </div>
        </div>

        <p className="text-center text-[11px] text-slate-500">
          The human facilitator desk acts as a safety and reliability fallback for the AI engine.
        </p>
      </div>
    </div>
  );
};
