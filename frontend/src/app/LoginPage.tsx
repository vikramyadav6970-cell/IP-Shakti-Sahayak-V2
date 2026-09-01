import React, { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { LogIn, UserPlus, Scale, AlertCircle, Loader2, ArrowLeft, Languages } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
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
    <div className="max-w-md mx-auto py-6 space-y-4">
      {/* Back to Home Button */}
      <div>
        <Link
          to="/"
          className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors gap-1 px-1 py-1 rounded-md"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Home</span>
        </Link>
      </div>

      <Card className="shadow-lg border-emerald-600/20">
        <CardHeader className="text-center space-y-2">
          <div className="w-12 h-12 rounded-xl bg-emerald-700 text-white flex items-center justify-center mx-auto shadow-md">
            <Scale className="w-6 h-6" />
          </div>
          <CardTitle className="text-xl">IP-SAKTI Sahayak Portal</CardTitle>
          <CardDescription>
            Account required to access verified IPR & Regulatory consultation.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Language Preference Selector */}
          <div className="space-y-1.5 p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/40">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-emerald-900 dark:text-emerald-300 flex items-center gap-1.5">
                <Languages className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                Default Consultation Language
              </label>
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                Sarvam AI
              </span>
            </div>
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="w-full h-9 px-2.5 text-xs rounded-md bg-white dark:bg-slate-900 border border-emerald-300/80 dark:border-emerald-700/60 text-slate-800 dark:text-slate-100 font-medium focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.flag} {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              You can also change language anytime mid-conversation in the chat header.
            </p>
          </div>

          {errorMessage && (
            <div
              role="alert"
              className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-2"
            >
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v as any); setErrorMessage(null); }}>
            <TabsList className="grid grid-cols-2 w-full mb-4">
              <TabsTrigger value="login">Sign In</TabsTrigger>
              <TabsTrigger value="register">Create Account</TabsTrigger>
            </TabsList>

            {/* TAB: LOGIN */}
            <TabsContent value="login">
              <form onSubmit={handleSubmitLogin(onLoginSubmit)} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Email Address</label>
                  <Input
                    type="email"
                    {...registerLogin("email")}
                    placeholder="user@example.com"
                    aria-invalid={Boolean(loginErrors.email)}
                  />
                  {loginErrors.email && (
                    <p className="text-[11px] text-destructive">{loginErrors.email.message}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Password</label>
                  <Input
                    type="password"
                    {...registerLogin("password")}
                    placeholder="••••••••"
                    aria-invalid={Boolean(loginErrors.password)}
                  />
                  {loginErrors.password && (
                    <p className="text-[11px] text-destructive">{loginErrors.password.message}</p>
                  )}
                </div>

                <Button type="submit" disabled={isLoading} className="w-full bg-emerald-700 hover:bg-emerald-800 text-white mt-2">
                  {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <LogIn className="w-4 h-4 mr-2" />}
                  Sign In
                </Button>
              </form>
            </TabsContent>

            {/* TAB: REGISTER (Streamlined: Name, Email, Password) */}
            <TabsContent value="register">
              <form onSubmit={handleSubmitRegister(onRegisterSubmit)} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Full Name</label>
                  <Input
                    type="text"
                    {...registerRegister("name")}
                    placeholder="Your Name"
                    aria-invalid={Boolean(registerErrors.name)}
                  />
                  {registerErrors.name && (
                    <p className="text-[11px] text-destructive">{registerErrors.name.message}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Email Address</label>
                  <Input
                    type="email"
                    {...registerRegister("email")}
                    placeholder="name@example.com"
                    aria-invalid={Boolean(registerErrors.email)}
                  />
                  {registerErrors.email && (
                    <p className="text-[11px] text-destructive">{registerErrors.email.message}</p>
                  )}
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Password (min 8 chars)</label>
                  <Input
                    type="password"
                    {...registerRegister("password")}
                    placeholder="••••••••"
                    aria-invalid={Boolean(registerErrors.password)}
                  />
                  {registerErrors.password && (
                    <p className="text-[11px] text-destructive">{registerErrors.password.message}</p>
                  )}
                </div>

                <Button type="submit" disabled={isLoading} className="w-full bg-emerald-700 hover:bg-emerald-800 text-white mt-2">
                  {isLoading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <UserPlus className="w-4 h-4 mr-2" />}
                  Create Account & Access
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>

        <CardFooter>
          <p className="text-[11px] text-center text-slate-500 w-full">
            All consultations are confidential and protected under DPDP principles.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};
