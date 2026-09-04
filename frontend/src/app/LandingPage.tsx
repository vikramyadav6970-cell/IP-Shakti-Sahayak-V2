import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  ShieldCheck,
  Globe,
  Lock,
  Award,
  Layers,
  ArrowRight,
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";
import { SacredTreeBackground } from "@/components/SacredTreeBackground";

export const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  const handleFeatureClick = (targetPath: string) => {
    if (!isAuthenticated) {
      navigate("/login", { state: { from: { pathname: targetPath } } });
    } else {
      navigate(targetPath);
    }
  };

  return (
    <div className="relative space-y-20 py-8 max-w-6xl mx-auto px-2 sm:px-4">
      {/* Sacred Tree Living Background Animation (Matches NyayAI dark ethereal aesthetic) */}
      <SacredTreeBackground growthDuration={4000} scale={1.22} treeOpacity={0.35} />

      {/* 1. HERO SECTION (Frosted glass chip, display typography, smooth emerald gradient) */}
      <section className="relative z-10 text-center space-y-6 pt-4 sm:pt-8 max-w-4xl mx-auto">
        {/* Ministry Badge — Ultra-Refined Luminous Glass Capsule */}
        <div className="inline-flex items-center p-[1.5px] rounded-full bg-gradient-to-r from-emerald-500/60 via-teal-400/50 to-emerald-500/60 shadow-[0_0_35px_rgba(16,185,129,0.3)] hover:shadow-[0_0_50px_rgba(16,185,129,0.55)] hover:scale-[1.02] transition-all duration-500 group">
          <div className="flex items-center gap-3 px-5 sm:px-6 py-2 rounded-full bg-gradient-to-r from-slate-950/95 via-[#031d16]/95 to-slate-950/95 backdrop-blur-2xl border border-white/5">
            {/* Pulsing Beacon Indicator */}
            <span className="relative flex h-2.5 w-2.5 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-gradient-to-r from-emerald-400 to-teal-300 shadow-[0_0_10px_#34d399]"></span>
            </span>

            {/* Glowing Ayush Seal Icon */}
            <Award className="w-4 h-4 text-emerald-400 shrink-0 group-hover:rotate-12 group-hover:scale-110 transition-transform duration-300 drop-shadow-[0_0_8px_rgba(52,211,153,0.6)]" />

            {/* Distinctive Typography Hierarchy */}
            <div className="flex items-center gap-2 whitespace-nowrap text-xs sm:text-xs">
              <span className="font-semibold text-emerald-300 tracking-wide font-display">Ministry of Ayush</span>
              <span className="text-emerald-500/60 font-bold">•</span>
              <span className="text-slate-300 font-medium tracking-wide">Legal & Regulatory Intelligence</span>
            </div>
          </div>
        </div>

        {/* Hero Title with Distinctive Display Font */}
        <h1 className="font-display text-4xl sm:text-6xl lg:text-6xl font-bold tracking-tight text-white leading-[1.12]">
          Authoritative AI Intelligence for{" "}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-300 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(52,211,153,0.55)]">
            Ayurveda & Herbal IPR
          </span>{" "}
          & Regulatory Compliance
        </h1>

        {/* Hero Subtitle with Refined Font Weight and Contrast */}
        <p className="font-sans text-base sm:text-lg text-slate-300/90 font-normal max-w-2xl mx-auto leading-relaxed tracking-normal">
          Accelerate patentability clearance, streamline ABS compliance, and navigate AYUSH regulatory licensing with source-verified legal intelligence.
        </p>

        {/* Action Button: Sleek Rectangular Dynamic Liquid Fill Button */}
        <div className="flex items-center justify-center pt-2">
          <button
            type="button"
            onClick={() => handleFeatureClick("/chat")}
            className="group relative overflow-hidden h-12 px-8 sm:px-9 rounded-xl text-white font-semibold text-sm cursor-pointer border border-emerald-400/50 bg-emerald-950/90 backdrop-blur-xl shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center justify-center"
          >
            {/* Dynamic Liquid Wave Fill from Left */}
            <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 scale-x-0 group-hover:scale-x-100 origin-left transition-transform duration-500 ease-out pointer-events-none" />

            {/* Foreground Content */}
            <span className="relative z-10 flex items-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
              <Sparkles className="w-4 h-4 text-amber-300 group-hover:text-amber-800 group-hover:rotate-12 transition-transform duration-300" />
              <span className="tracking-wide">{isAuthenticated ? "Launch AI Consultation" : "Sign Up"}</span>
              <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
            </span>
          </button>
        </div>
      </section>

      {/* 2. CORE MODULES GRID (Interactive Frosted Glass Cards with Hover Elevation & Glow) */}
      <section className="relative z-10 space-y-7">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Core IP & Regulatory Decision Modules
          </h2>
          <p className="font-sans text-xs sm:text-sm text-slate-300/80 font-normal">
            Engineered for AYUSH innovators, manufacturers, and researchers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: AI Formulation Diagnostic & Licensing */}
          <div
            onClick={() => handleFeatureClick("/chat")}
            className="glass-landing-card group relative p-7 rounded-2xl flex flex-col justify-between overflow-hidden cursor-pointer"
          >
            {/* Top accent glow line on hover */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 flex items-center justify-center group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-400/50 transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.15)]">
                  <Layers className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/25">
                  Licensing AI
                </span>
              </div>

              <div className="space-y-2">
                <h3 className="font-display text-base font-bold text-white group-hover:text-emerald-300 transition-colors tracking-tight">
                  AI Formulation Diagnostic & Licensing
                </h3>
                <p className="font-sans text-xs text-slate-300/85 font-normal leading-relaxed">
                  Instantly classify herbal formulations across 6 statutory AYUSH categories. Auto-map Form 25-D licensing pathways, Rule 158B safety clearances, and FSSAI Ayush Aahara standards.
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-6 pt-4 border-t border-white/10 space-y-3">
              <div className="flex flex-wrap gap-1.5 opacity-85 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-emerald-950/70 text-emerald-300 border border-emerald-500/30">
                  Form 25-D
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  Rule 158B
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  Ayush Aahara
                </span>
              </div>
              <div className="flex items-center text-xs font-semibold text-emerald-400 transform translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Run Product Diagnostic</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* Card 2: Section 3(p) Patentability & Prior Art Clearance */}
          <div
            onClick={() => handleFeatureClick("/chat?intent=PATENTABILITY")}
            className="glass-landing-card group relative p-7 rounded-2xl flex flex-col justify-between overflow-hidden cursor-pointer"
          >
            {/* Top accent glow line on hover */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-amber-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/25 flex items-center justify-center group-hover:scale-110 group-hover:bg-amber-500/20 group-hover:border-amber-400/50 transition-all duration-300 shadow-[0_0_20px_rgba(245,158,11,0.15)]">
                  <ShieldCheck className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/25">
                  Patent Radar
                </span>
              </div>

              <div className="space-y-2">
                <h3 className="font-display text-base font-bold text-white group-hover:text-amber-300 transition-colors tracking-tight">
                  Section 3(p) Patentability Radar
                </h3>
                <p className="font-sans text-xs text-slate-300/85 font-normal leading-relaxed">
                  Screen herbal innovations against 400,000+ TKDL traditional knowledge records. Discover non-obvious synergistic formulations to overcome Section 3(p) patent rejections.
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-6 pt-4 border-t border-white/10 space-y-3">
              <div className="flex flex-wrap gap-1.5 opacity-85 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-amber-950/70 text-amber-300 border border-amber-500/30">
                  Section 3(p)
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  TKDL Prior Art
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  Synergy Validation
                </span>
              </div>
              <div className="flex items-center text-xs font-semibold text-amber-400 transform translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Check Patent Feasibility</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* Card 3: RAG Legal Consultation Assistant */}
          <div
            onClick={() => handleFeatureClick("/chat")}
            className="glass-landing-card group relative p-7 rounded-2xl flex flex-col justify-between overflow-hidden cursor-pointer"
          >
            {/* Top accent glow line on hover */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-teal-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-xl bg-teal-500/10 text-teal-400 border border-teal-500/25 flex items-center justify-center group-hover:scale-110 group-hover:bg-teal-500/20 group-hover:border-teal-400/50 transition-all duration-300 shadow-[0_0_20px_rgba(20,184,166,0.15)]">
                  <Sparkles className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full bg-teal-500/10 text-teal-300 border border-teal-500/25">
                  Verified Law
                </span>
              </div>

              <div className="space-y-2">
                <h3 className="font-display text-base font-bold text-white group-hover:text-teal-300 transition-colors tracking-tight">
                  Grounded Legal & Regulatory RAG
                </h3>
                <p className="font-sans text-xs text-slate-300/85 font-normal leading-relaxed">
                  Ask intricate legal queries and receive source-grounded answers with direct citations to Official Gazettes, CDSCO notifications, and WIPO Lex treaties — with zero hallucination.
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-6 pt-4 border-t border-white/10 space-y-3">
              <div className="flex flex-wrap gap-1.5 opacity-85 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-teal-950/70 text-teal-300 border border-teal-500/30">
                  Official Gazettes
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  Statutory Citations
                </span>
                <span className="text-[10px] font-medium tracking-wide px-2.5 py-1 rounded-lg bg-white/5 text-slate-300 border border-white/10">
                  Zero Hallucination
                </span>
              </div>
              <div className="flex items-center text-xs font-semibold text-teal-400 transform translate-y-1 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Start Legal Consultation</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. TRUST & SECURITY SECTION (Frosted Glass Panel with Ambient Depth) */}
      <section className="relative z-10 p-8 sm:p-12 rounded-3xl bg-slate-950/60 backdrop-blur-2xl border border-white/10 space-y-8 shadow-[0_12px_40px_0_rgba(0,0,0,0.5)]">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-950/70 backdrop-blur-xl text-emerald-300 border border-emerald-500/40 text-xs font-semibold shadow-md">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Institutional Trust Architecture</span>
          </div>
          <h2 className="font-display text-2xl sm:text-4xl font-bold text-white tracking-tight">
            Built for Legal & Regulatory Rigor
          </h2>
          <p className="font-sans text-sm sm:text-base text-slate-300/90 font-normal leading-relaxed">
            Adhering strictly to statutory provisions for traditional knowledge safeguarding.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 text-center">
          {/* Card 1 */}
          <div className="group relative space-y-4 p-7 sm:p-8 rounded-2xl bg-white/[0.03] backdrop-blur-md border border-white/[0.08] hover:border-emerald-500/40 hover:bg-white/[0.06] hover:-translate-y-1 hover:shadow-[0_12px_30px_-10px_rgba(16,185,129,0.2)] transition-all duration-300 ease-out overflow-hidden">
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all duration-300 pointer-events-none" />

            {/* Centered Icon in Glass Container */}
            <div className="w-13 h-13 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-400/40 transition-all duration-300 shadow-inner">
              <ShieldCheck className="w-6 h-6" />
            </div>

            <h3 className="font-display text-base font-bold text-white tracking-tight">
              Zero Hallucination Grounding
            </h3>

            <p className="font-sans text-xs sm:text-sm text-slate-300/85 font-normal leading-relaxed">
              Every sentence in consultations is grounded in official gazettes and statutory provisions. Unsupported citations are filtered.
            </p>
          </div>

          {/* Card 2 */}
          <div className="group relative space-y-4 p-7 sm:p-8 rounded-2xl bg-white/[0.03] backdrop-blur-md border border-white/[0.08] hover:border-emerald-500/40 hover:bg-white/[0.06] hover:-translate-y-1 hover:shadow-[0_12px_30px_-10px_rgba(16,185,129,0.2)] transition-all duration-300 ease-out overflow-hidden">
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all duration-300 pointer-events-none" />

            {/* Centered Icon in Glass Container */}
            <div className="w-13 h-13 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-400/40 transition-all duration-300 shadow-inner">
              <Lock className="w-6 h-6" />
            </div>

            <h3 className="font-display text-base font-bold text-white tracking-tight">
              DPDP-Compliant & Confidential
            </h3>

            <p className="font-sans text-xs sm:text-sm text-slate-300/85 font-normal leading-relaxed">
              Proprietary formulation data is anonymized before AI processing. Consultation sessions are cryptographically logged for auditability.
            </p>
          </div>

          {/* Card 3 */}
          <div className="group relative space-y-4 p-7 sm:p-8 rounded-2xl bg-white/[0.03] backdrop-blur-md border border-white/[0.08] hover:border-emerald-500/40 hover:bg-white/[0.06] hover:-translate-y-1 hover:shadow-[0_12px_30px_-10px_rgba(16,185,129,0.2)] transition-all duration-300 ease-out overflow-hidden">
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-emerald-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all duration-300 pointer-events-none" />

            {/* Centered Icon in Glass Container */}
            <div className="w-13 h-13 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-400/40 transition-all duration-300 shadow-inner">
              <Globe className="w-6 h-6" />
            </div>

            <h3 className="font-display text-base font-bold text-white tracking-tight">
              Human Expert Escalation Desk
            </h3>

            <p className="font-sans text-xs sm:text-sm text-slate-300/85 font-normal leading-relaxed">
              Complex queries or low-confidence determinations can be escalated directly to IP Facilitators for institutional review.
            </p>
          </div>
        </div>
      </section>

      {/* 4. FINAL CALL TO ACTION (Frosted Glass Container with Radial Ambient Glow) */}
      <section className="relative z-10 text-center space-y-5 py-12 px-6 sm:px-12 rounded-3xl bg-gradient-to-b from-slate-900/60 to-slate-950/85 backdrop-blur-2xl border border-white/10 shadow-[0_12px_40px_0_rgba(0,0,0,0.5)] max-w-3xl mx-auto overflow-hidden">
        {/* Ambient glow backdrop */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <h2 className="font-display text-2xl sm:text-4xl font-bold text-white tracking-tight leading-tight relative z-10">
          Ready to Accelerate Your Ayurvedic Innovation?
        </h2>
        <p className="font-sans text-sm sm:text-base text-slate-300/90 font-normal leading-relaxed max-w-xl mx-auto relative z-10">
          Create an account to access the complete suite of IPR, ABS, and Regulatory decision support tools.
        </p>
        <div className="pt-2 relative z-10">
          <button
            type="button"
            onClick={() => navigate(isAuthenticated ? "/chat" : "/login")}
            className="group relative overflow-hidden h-12 px-8 sm:px-9 rounded-xl text-white font-semibold text-sm cursor-pointer border border-emerald-400/50 bg-emerald-950/90 backdrop-blur-xl shadow-[0_0_25px_rgba(16,185,129,0.35)] group-hover:shadow-[0_0_35px_rgba(16,185,129,0.65)] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center justify-center mx-auto"
          >
            {/* Dynamic Liquid Wave Fill from Left */}
            <span className="absolute inset-0 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 scale-x-0 group-hover:scale-x-100 origin-left transition-transform duration-500 ease-out pointer-events-none" />

            {/* Foreground Content */}
            <span className="relative z-10 flex items-center gap-2 whitespace-nowrap text-white group-hover:text-slate-950 font-bold transition-colors duration-300">
              <Sparkles className="w-4 h-4 text-amber-300 group-hover:text-amber-800 group-hover:rotate-12 transition-transform duration-300" />
              <span className="tracking-wide">{isAuthenticated ? "Go to Consultation Portal" : "Sign Up & Start Consultation"}</span>
              <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
            </span>
          </button>
        </div>
      </section>
    </div>
  );
};
