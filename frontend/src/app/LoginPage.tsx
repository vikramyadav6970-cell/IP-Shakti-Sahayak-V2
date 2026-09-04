import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  AlertCircle,
  Loader2,
  ArrowLeft,
  Languages,
  Sparkles,
  LogOut,
  ArrowRight,
  ShieldCheck,
  Mail,
  Lock,
  Eye,
  EyeOff,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/useAuthStore";
import { useChatStore } from "@/store/useChatStore";
import { authService } from "@/services/authService";
import { SUPPORTED_LANGUAGES } from "@/components/chat/LanguageSelector";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;
type RegisterFormValues = z.infer<typeof registerSchema>;

export const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"login" | "register">("login");
  const [rememberMe, setRememberMe] = useState(true);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { setAuth, setToken, isAuthenticated, user, clearAuth } = useAuthStore();
  const { selectedLanguage, setSelectedLanguage } = useChatStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/chat";

  const {
    register: registerLogin,
    handleSubmit: handleSubmitLogin,
    formState: { errors: loginErrors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
  });

  const {
    register: registerRegister,
    handleSubmit: handleSubmitRegister,
    formState: { errors: registerErrors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
  });

  const onLoginSubmit = async (data: LoginFormValues) => {
    setErrorMessage(null);
    setIsLoading(true);
    try {
      const tokens = await authService.login(data);
      setToken(tokens.access_token);
      const user = await authService.getMe();
      setAuth(user, tokens.access_token);
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to log in. Please check credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const onRegisterSubmit = async (data: RegisterFormValues) => {
    setErrorMessage(null);
    setIsLoading(true);
    try {
      await authService.register({
        name: data.name,
        email: data.email,
        password: data.password,
        role: "USER",
      });

      const tokens = await authService.login({ email: data.email, password: data.password });
      setToken(tokens.access_token);
      const user = await authService.getMe();
      setAuth(user, tokens.access_token);
      navigate(from, { replace: true });
    } catch (err: any) {
      setErrorMessage(err.message || "Registration failed. Email may already be in use.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 h-screen w-screen overflow-hidden bg-[#030712] text-slate-100 flex items-center justify-center p-4 sm:p-6 selection:bg-emerald-500 selection:text-white">
      {/* Ambient background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-500/10 rounded-full blur-[130px] pointer-events-none" />

      {/* Centered Fixed Card */}
      <div className="relative z-10 w-full max-w-md p-6 sm:p-8 rounded-3xl bg-slate-950/90 backdrop-blur-2xl border border-white/10 shadow-[0_20px_60px_rgba(0,0,0,0.75)] flex flex-col justify-between max-h-[95vh] overflow-hidden">
        
        {/* Header Branding & Navigation */}
        <div className="flex items-center justify-between gap-3 pb-4 border-b border-white/5 shrink-0">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="relative w-9 h-9 rounded-xl p-[1.5px] bg-gradient-to-br from-amber-400 via-emerald-400 to-teal-500 shadow-[0_0_15px_rgba(16,185,129,0.35)] group-hover:scale-105 transition-all shrink-0">
              <div className="w-full h-full rounded-[10px] overflow-hidden bg-slate-950 p-1 flex items-center justify-center">
                <img
                  src="/ayush-logo.svg"
                  alt="Ministry of Ayush - IP-SAKTI Sahayak Emblem"
                  className="w-full h-full object-contain select-none"
                />
              </div>
            </div>
            <div>
              <span className="font-display text-sm font-bold tracking-tight text-white flex items-center gap-1">
                IP-SAKTI
                <span className="text-emerald-400 font-bold">Sahayak</span>
              </span>
              <p className="text-[10px] text-slate-400 font-medium tracking-wider">
                Ministry of Ayush
              </p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
              <Languages className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <select
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
                aria-label="Select Language"
                className="bg-transparent text-xs text-slate-300 font-medium focus:outline-none cursor-pointer"
              >
                {SUPPORTED_LANGUAGES.map((lang) => (
                  <option key={lang.code} value={lang.code} className="bg-slate-900 text-white">
                    {lang.nativeName}
                  </option>
                ))}
              </select>
            </div>

            <Link
              to="/"
              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Home</span>
            </Link>
          </div>
        </div>

        {/* Content Area */}
        <div className="py-4 overflow-y-auto pr-0.5">
          {isAuthenticated ? (
            <div className="space-y-5 animate-in fade-in zoom-in-95 duration-300">
              <div className="space-y-1.5 text-center">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950/70 border border-emerald-500/30 text-emerald-300 text-xs font-medium mx-auto">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400"></span>
                  </span>
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Authenticated Session</span>
                </div>
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Welcome back!
                </h1>
                <p className="text-xs text-slate-300/80">
                  You are actively signed into IP-SAKTI Sahayak.
                </p>
              </div>

              {/* User Profile Card */}
              <div className="p-3.5 rounded-2xl bg-slate-900/70 border border-white/10 backdrop-blur-xl flex items-center gap-3.5 shadow-lg">
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 text-white flex items-center justify-center font-bold text-base shadow-md border border-emerald-400/30 shrink-0">
                  {(user?.name || "User").charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-bold text-white truncate">{user?.name || "Ayush Researcher"}</h3>
                  <p className="text-[11px] text-slate-400 truncate">{user?.email || "user@ayush-ip.gov.in"}</p>
                  <span className="inline-block mt-0.5 px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider">
                    {user?.role || "USER"}
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-2.5 pt-1">
                <button
                  type="button"
                  onClick={() => navigate(from || "/chat")}
                  className="group relative overflow-hidden w-full h-12 rounded-xl text-white font-semibold text-sm cursor-pointer border border-emerald-400/50 bg-emerald-950/90 backdrop-blur-xl shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300 flex items-center justify-center"
                >
                  <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                  <span className="relative z-10 flex items-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
                    <Sparkles className="w-4 h-4 text-amber-300 group-hover:text-amber-800 group-hover:rotate-12 transition-transform duration-300" />
                    <span className="tracking-wide">Continue to AI Consultation</span>
                    <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => clearAuth()}
                  className="w-full h-10 rounded-xl text-xs font-semibold text-slate-300 hover:text-white bg-slate-900/60 hover:bg-slate-900 border border-white/10 hover:border-destructive/40 transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5 text-slate-400" />
                  <span>Sign Out & Switch Account</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Title and Subtitle */}
              <div className="space-y-1 text-center">
                <h1 className="font-display text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  {activeTab === "login" ? "Welcome back!" : "Create an account"}
                </h1>
                <p className="text-xs text-slate-300/80 font-normal leading-relaxed">
                  {activeTab === "login"
                    ? "Where ancient botanical wisdom meets legal intelligence."
                    : "Join the platform safeguarding AYUSH innovations."}
                </p>
              </div>

              {/* Error banner */}
              {errorMessage && (
                <div className="p-3 rounded-xl bg-destructive/15 border border-destructive/30 text-destructive text-xs flex items-center gap-2 animate-in fade-in duration-200">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {activeTab === "login" ? (
                <form onSubmit={handleSubmitLogin(onLoginSubmit)} className="space-y-3.5">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Email</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Mail className="w-4 h-4" />
                      </div>
                      <Input
                        type="email"
                        placeholder="Enter your email"
                        {...registerLogin("email")}
                        className="pl-10 h-10.5 text-sm bg-slate-950/70 border-slate-800 text-white placeholder:text-slate-500 rounded-xl focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 transition-all"
                      />
                    </div>
                    {loginErrors.email && (
                      <p className="text-[11px] text-destructive font-medium pl-1">
                        {loginErrors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Password</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Lock className="w-4 h-4" />
                      </div>
                      <Input
                        type={showLoginPassword ? "text" : "password"}
                        placeholder="••••••••••••"
                        {...registerLogin("password")}
                        className="pl-10 pr-10 h-10.5 text-sm bg-slate-950/70 border-slate-800 text-white placeholder:text-slate-500 rounded-xl focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowLoginPassword(!showLoginPassword)}
                        aria-label={showLoginPassword ? "Hide password" : "Show password"}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      >
                        {showLoginPassword ? (
                          <EyeOff className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    {loginErrors.password && (
                      <p className="text-[11px] text-destructive font-medium pl-1">
                        {loginErrors.password.message}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between pt-0.5 text-xs text-slate-300">
                    <label className="flex items-center gap-2 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        className="w-3.5 h-3.5 rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500 focus:ring-offset-0 cursor-pointer accent-emerald-500"
                      />
                      <span>Remember me</span>
                    </label>

                    <span className="text-slate-400 hover:text-emerald-400 transition-colors cursor-pointer">
                      Forgot password?
                    </span>
                  </div>

                  {/* High-Contrast Rectangular Log in Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="group relative overflow-hidden w-full h-12 px-8 sm:px-9 rounded-xl text-white font-semibold text-sm cursor-pointer border border-emerald-400/50 bg-emerald-950/90 backdrop-blur-xl shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300 flex items-center justify-center mt-3"
                  >
                    {/* Smooth glowing fill without bar sweep */}
                    <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                    {/* Foreground Content */}
                    <span className="relative z-10 flex items-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-white group-hover:text-slate-950" />
                          <span className="tracking-wide">Signing In...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-amber-300 group-hover:text-amber-800 group-hover:rotate-12 transition-transform duration-300" />
                          <span className="tracking-wide">Log In</span>
                          <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                        </>
                      )}
                    </span>
                  </button>

                  <div className="pt-3 border-t border-white/10 text-center">
                    <p className="text-xs text-slate-400">
                      Don't have an account?{" "}
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab("register");
                          setErrorMessage(null);
                        }}
                        className="font-bold text-white hover:text-emerald-400 transition-colors underline underline-offset-2 cursor-pointer"
                      >
                        Sign up
                      </button>
                    </p>
                  </div>
                </form>
              ) : (
                <form onSubmit={handleSubmitRegister(onRegisterSubmit)} className="space-y-3.5">
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Full Name</label>
                    <Input
                      placeholder="Dr. Vaidya / Researcher"
                      {...registerRegister("name")}
                      className="h-10.5 text-sm bg-slate-950/70 border-slate-800 text-white placeholder:text-slate-500 rounded-xl focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 transition-all"
                    />
                    {registerErrors.name && (
                      <p className="text-[11px] text-destructive font-medium pl-1">
                        {registerErrors.name.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Email Address</label>
                    <Input
                      type="email"
                      placeholder="name@example.com"
                      {...registerRegister("email")}
                      className="h-10.5 text-sm bg-slate-950/70 border-slate-800 text-white placeholder:text-slate-500 rounded-xl focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 transition-all"
                    />
                    {registerErrors.email && (
                      <p className="text-[11px] text-destructive font-medium pl-1">
                        {registerErrors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-medium text-slate-300">Password</label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                        <Lock className="w-4 h-4" />
                      </div>
                      <Input
                        type={showRegisterPassword ? "text" : "password"}
                        placeholder="Minimum 8 characters"
                        {...registerRegister("password")}
                        className="pl-10 pr-10 h-10.5 text-sm bg-slate-950/70 border-slate-800 text-white placeholder:text-slate-500 rounded-xl focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/80 transition-all"
                      />
                      <button
                        type="button"
                        onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                        aria-label={showRegisterPassword ? "Hide password" : "Show password"}
                        className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
                      >
                        {showRegisterPassword ? (
                          <EyeOff className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    {registerErrors.password && (
                      <p className="text-[11px] text-destructive font-medium pl-1">
                        {registerErrors.password.message}
                      </p>
                    )}
                  </div>

                  {/* Rectangular Create Account Button */}
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="group relative overflow-hidden w-full h-12 px-8 sm:px-9 rounded-xl text-white font-semibold text-sm cursor-pointer border border-emerald-400/50 bg-emerald-950/90 backdrop-blur-xl shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300 flex items-center justify-center mt-3"
                  >
                    {/* Smooth glowing fill without bar sweep */}
                    <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                    {/* Foreground Content */}
                    <span className="relative z-10 flex items-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin text-white group-hover:text-slate-950" />
                          <span className="tracking-wide">Creating Account...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-4 h-4 text-amber-300 group-hover:text-amber-800 group-hover:rotate-12 transition-transform duration-300" />
                          <span className="tracking-wide">Create Account</span>
                          <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                        </>
                      )}
                    </span>
                  </button>

                  <div className="pt-3 border-t border-white/10 text-center">
                    <p className="text-xs text-slate-400">
                      Already have an account?{" "}
                      <button
                        type="button"
                        onClick={() => {
                          setActiveTab("login");
                          setErrorMessage(null);
                        }}
                        className="font-bold text-white hover:text-emerald-400 transition-colors underline underline-offset-2 cursor-pointer"
                      >
                        Sign in
                      </button>
                    </p>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>

        {/* Footer Security Badge */}
        <div className="pt-3 border-t border-slate-800/80 text-center shrink-0">
          <p className="text-[10px] sm:text-[11px] text-slate-400 font-medium">
            Protected by Ayush Institutional Authentication &amp; DPDP Standards
          </p>
        </div>

      </div>
    </div>
  );
};
