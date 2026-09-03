import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  LogIn,
  UserPlus,
  AlertCircle,
  Loader2,
  ArrowLeft,
  Languages,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useAuthStore } from "@/store/useAuthStore";
import { useChatStore } from "@/store/useChatStore";
import { authService } from "@/services/authService";
import { SUPPORTED_LANGUAGES } from "@/components/chat/LanguageSelector";
import { ThemeToggle } from "@/components/common/ThemeToggle";

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
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { setAuth, setToken } = useAuthStore();
  const { selectedLanguage, setSelectedLanguage } = useChatStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as any)?.from?.pathname || "/chat";

  const {
    register: registerLogin,
    handleSubmit: handleSubmitLogin,
    setValue: setLoginValue,
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

  const fillDemoUser = () => {
    setLoginValue("email", "user@ayush-ip.gov.in");
    setLoginValue("password", "AyushIP@2026");
  };

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

      // Auto login after successful registration
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
    <div className="h-screen w-screen bg-slate-100 dark:bg-[#030712] overflow-hidden p-3 sm:p-5 flex flex-col justify-between text-slate-900 dark:text-white selection:bg-emerald-500 selection:text-white transition-colors duration-200">
      {/* 1. Top Header Bar */}
      <header className="w-full flex items-center justify-between pb-2 shrink-0 border-b border-slate-200 dark:border-slate-800/80 px-1">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-600 to-teal-700 text-white flex items-center justify-center font-bold text-xs shadow-md border border-emerald-400/30">
            IP
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-white block leading-tight">
              IP-SAKTI Sahayak
            </span>
            <span className="text-[10px] text-slate-500 dark:text-slate-400 block leading-tight">
              Ministry of Ayush · Government of India
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <ThemeToggle />
          <Link
            to="/"
            className="inline-flex items-center text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 hover:border-slate-400 dark:hover:border-slate-700 shadow-xs cursor-pointer"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>
        </div>
      </header>

      {/* 2. Main Body: Separated 40:60 Split Fitting Window Perfectly */}
      <main className="flex-1 w-full my-3 flex flex-col md:flex-row gap-4 sm:gap-5 overflow-hidden min-h-0">
        
        {/* =========================================================================
            PORTION 1: 40% RATIO — NORMAL 2D ANIMATED CHARAKA WITH REVOLVING CHAKRA
            ========================================================================= */}
        <section className="w-full md:w-[40%] h-full rounded-2xl overflow-hidden bg-slate-900 dark:bg-[#030712] border border-slate-300 dark:border-slate-800/90 shadow-2xl relative flex flex-col justify-end p-5 min-h-0">
          
          {/* Ambient Blue & Cyan Glow Backdrop */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-72 h-72 rounded-full bg-cyan-500/15 blur-3xl" />
            <div className="w-48 h-48 rounded-full bg-blue-600/20 blur-2xl" />
          </div>

          {/* REVOLVING BLUE / CYAN CHAKRA (HALO) BEHIND CHARAKA */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden">
            {/* Outer Rotating Celestial Ring */}
            <div 
              className="w-[340px] h-[340px] sm:w-[380px] sm:h-[380px] rounded-full border-2 border-dashed border-cyan-400/40 relative flex items-center justify-center"
              style={{ animation: "haloSpin 24s linear infinite" }}
            >
              {/* Orbital glowing nodes on the revolving ring */}
              <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-cyan-400 shadow-[0_0_12px_#38bdf8]" />
              <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-blue-500 shadow-[0_0_12px_#3b82f6]" />
              <div className="absolute top-1/2 -left-2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-teal-400 shadow-[0_0_10px_#2dd4bf]" />
              <div className="absolute top-1/2 -right-2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-sky-400 shadow-[0_0_10px_#38bdf8]" />
              
              {/* Concentric Geometric Ring */}
              <div className="w-[270px] h-[270px] sm:w-[300px] sm:h-[300px] rounded-full border border-cyan-500/30 border-dotted" />
            </div>

            {/* Inner Counter-Revolving Sacred Mandala Ring */}
            <div 
              className="absolute w-[220px] h-[220px] sm:w-[250px] sm:h-[250px] rounded-full border border-blue-400/50 flex items-center justify-center"
              style={{ animation: "haloSpinReverse 16s linear infinite" }}
            >
              <div className="w-full h-full rounded-full border border-cyan-300/25 rotate-45" />
              <div className="absolute inset-2 rounded-full border border-teal-400/30 rotate-12" />
            </div>
          </div>

          {/* NORMAL 2D ANIMATED CARTOONIC CHARAKA RISHI */}
          <div className="absolute inset-0 flex items-center justify-center overflow-hidden pointer-events-none">
            <img
              src="/charaka-animated.jpg"
              alt="Maharishi Charaka — The Father of Ayurveda"
              className="w-[90%] h-[90%] object-contain object-center transition-transform duration-700 ease-out"
              style={{
                animation: "charakaFloat 12s ease-in-out infinite alternate",
              }}
            />
          </div>

          {/* Gentle cinematic bottom vignette */}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/95 via-transparent to-transparent pointer-events-none" />

          {/* Clean minimal floating caption at bottom */}
          <div className="relative z-10 px-3.5 py-2.5 rounded-xl bg-slate-950/85 backdrop-blur-md border border-emerald-500/30 shadow-lg text-white">
            <h3 className="text-sm font-bold text-white tracking-tight">Maharishi Charaka</h3>
            <p className="text-[11px] font-semibold text-emerald-400">The Father of Ayurveda</p>
          </div>
        </section>

        {/* =========================================================================
            PORTION 2: 60% RATIO — COMPACT, ELEGANT LOGIN/SIGNUP CARD
            ========================================================================= */}
        <section className="w-full md:w-[60%] h-full flex items-center justify-center p-3 sm:p-6 min-h-0">
          <div className="w-full max-w-[500px] rounded-2xl bg-white dark:bg-slate-900/95 border border-slate-200 dark:border-slate-800 shadow-2xl p-7 sm:p-8 backdrop-blur-xl flex flex-col justify-between space-y-5 text-slate-900 dark:text-white transition-colors duration-200">
            
            <div className="space-y-4 sm:space-y-5">
              {/* Header & Language Row */}
              <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800/90 pb-3.5">
                <div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                    {activeTab === "login" ? "Sign In" : "Create Account"}
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                    {activeTab === "login" ? "Access your consultation dashboard" : "Register your Ayush research profile"}
                  </p>
                </div>

                {/* Language Selector */}
                <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-800">
                  <Languages className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="bg-transparent text-xs text-slate-800 dark:text-slate-200 font-medium focus:outline-none cursor-pointer"
                  >
                    {SUPPORTED_LANGUAGES.map((lang) => (
                      <option key={lang.code} value={lang.code} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                        {lang.nativeName}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Error Message */}
              {errorMessage && (
                <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}

              {/* Tabs: Login / Register */}
              <Tabs
                value={activeTab}
                onValueChange={(v) => {
                  setActiveTab(v as any);
                  setErrorMessage(null);
                }}
                className="w-full space-y-4"
              >
                <TabsList className="grid grid-cols-2 w-full bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 p-1 rounded-xl h-11">
                  <TabsTrigger
                    value="login"
                    className="rounded-lg text-xs sm:text-sm font-bold text-slate-600 dark:text-slate-400 data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-600 data-[state=active]:to-teal-600 data-[state=active]:text-white transition-all cursor-pointer h-9"
                  >
                    <LogIn className="w-3.5 h-3.5 mr-1.5" />
                    Sign In
                  </TabsTrigger>
                  <TabsTrigger
                    value="register"
                    className="rounded-lg text-xs sm:text-sm font-bold text-slate-600 dark:text-slate-400 data-[state=active]:bg-gradient-to-r data-[state=active]:from-emerald-600 data-[state=active]:to-teal-600 data-[state=active]:text-white transition-all cursor-pointer h-9"
                  >
                    <UserPlus className="w-3.5 h-3.5 mr-1.5" />
                    Create Account
                  </TabsTrigger>
                </TabsList>

                {/* TAB 1: SIGN IN */}
                <TabsContent value="login" className="space-y-3.5 mt-0">
                  <form onSubmit={handleSubmitLogin(onLoginSubmit)} className="space-y-3.5">
                    <div className="space-y-1.5">
                      <label className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">
                        Email Address
                      </label>
                      <Input
                        type="email"
                        placeholder="name@example.com"
                        {...registerLogin("email")}
                        className="h-10 sm:h-10.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-950/90 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-emerald-500"
                      />
                      {loginErrors.email && (
                        <p className="text-[11px] text-destructive font-medium">
                          {loginErrors.email.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <label className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">
                          Password
                        </label>
                        <button
                          type="button"
                          onClick={fillDemoUser}
                          className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 underline underline-offset-2 cursor-pointer"
                        >
                          Autofill Demo
                        </button>
                      </div>
                      <Input
                        type="password"
                        placeholder="••••••••••••"
                        {...registerLogin("password")}
                        className="h-10 sm:h-10.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-950/90 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-emerald-500"
                      />
                      {loginErrors.password && (
                        <p className="text-[11px] text-destructive font-medium">
                          {loginErrors.password.message}
                        </p>
                      )}
                    </div>

                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-11 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-emerald-900/30 transition-all cursor-pointer flex items-center justify-center gap-2 mt-3"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Signing In...</span>
                        </>
                      ) : (
                        <>
                          <LogIn className="w-4 h-4" />
                          <span>Sign In to Sahayak</span>
                        </>
                      )}
                    </Button>
                  </form>
                </TabsContent>

                {/* TAB 2: CREATE ACCOUNT */}
                <TabsContent value="register" className="space-y-3 mt-0">
                  <form onSubmit={handleSubmitRegister(onRegisterSubmit)} className="space-y-3">
                    <div className="space-y-1">
                      <label className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">Full Name</label>
                      <Input
                        placeholder="Dr. Vaidya / Researcher"
                        {...registerRegister("name")}
                        className="h-9.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-950/90 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-emerald-500"
                      />
                      {registerErrors.name && (
                        <p className="text-[11px] text-destructive font-medium">
                          {registerErrors.name.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">Email Address</label>
                      <Input
                        type="email"
                        placeholder="name@example.com"
                        {...registerRegister("email")}
                        className="h-9.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-950/90 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-emerald-500"
                      />
                      {registerErrors.email && (
                        <p className="text-[11px] text-destructive font-medium">
                          {registerErrors.email.message}
                        </p>
                      )}
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs sm:text-sm font-medium text-slate-700 dark:text-slate-300">Password</label>
                      <Input
                        type="password"
                        placeholder="Min 8 characters"
                        {...registerRegister("password")}
                        className="h-9.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-950/90 border-slate-300 dark:border-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:border-emerald-500"
                      />
                      {registerErrors.password && (
                        <p className="text-[11px] text-destructive font-medium">
                          {registerErrors.password.message}
                        </p>
                      )}
                    </div>

                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-10.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs sm:text-sm shadow-lg shadow-emerald-900/30 transition-all cursor-pointer flex items-center justify-center gap-2 mt-2"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Creating Account...</span>
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-4 h-4" />
                          <span>Create Account</span>
                        </>
                      )}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </div>

            <div className="text-center pt-2.5 border-t border-slate-200 dark:border-slate-800/80">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Protected by Ayush Institutional Authentication
              </p>
            </div>
          </div>
        </section>
      </main>

      <style>{`
        @keyframes haloSpin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        @keyframes haloSpinReverse {
          from {
            transform: rotate(360deg);
          }
          to {
            transform: rotate(0deg);
          }
        }
        @keyframes charakaFloat {
          0% {
            transform: scale(1.01) translateY(0px);
          }
          50% {
            transform: scale(1.04) translateY(-5px);
          }
          100% {
            transform: scale(1.01) translateY(0px);
          }
        }
      `}</style>
    </div>
  );
};
