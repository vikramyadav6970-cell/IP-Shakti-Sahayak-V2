import React, { useState, useEffect, useRef } from "react";
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
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/useAuthStore";
import { SacredTreeBackground } from "@/components/SacredTreeBackground";

interface StreamingTypewriterProps {
  text: string;
  isActive: boolean;
  delay?: number;
  speed?: number;
  triggerKey?: number;
}

const StreamingTypewriter: React.FC<StreamingTypewriterProps> = ({
  text,
  isActive,
  delay = 0,
  speed = 110,
  triggerKey = 0,
}) => {
  const [displayedText, setDisplayedText] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    if (!isActive) return;

    const words = text.split(" ");
    let timer: NodeJS.Timeout;
    let interval: NodeJS.Timeout;

    setDisplayedText("");
    setIsTyping(true);

    timer = setTimeout(() => {
      let currentIdx = 1;
      setDisplayedText(words[0] || "");

      interval = setInterval(() => {
        if (currentIdx < words.length) {
          currentIdx++;
          setDisplayedText(words.slice(0, currentIdx).join(" "));
        } else {
          setIsTyping(false);
          clearInterval(interval);
        }
      }, speed);
    }, delay);

    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, [isActive, text, delay, speed, triggerKey]);

  return (
    <span>
      {displayedText}
      {isTyping && (
        <span className="inline-block w-1.5 h-3.5 bg-emerald-400 align-middle ml-1 rounded-xs animate-pulse shadow-xs shadow-emerald-400" />
      )}
    </span>
  );
};

export const LandingPage: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const trustSectionRef = useRef<HTMLElement>(null);
  const [trustInView, setTrustInView] = useState(false);
  const [cardTriggers, setCardTriggers] = useState<{ [key: number]: number }>({ 1: 0, 2: 0, 3: 0 });

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTrustInView(true);
        }
      },
      { threshold: 0.15 }
    );

    if (trustSectionRef.current) {
      observer.observe(trustSectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const handleRetrigger = (cardNum: number) => {
    setCardTriggers((prev) => ({ ...prev, [cardNum]: prev[cardNum] + 1 }));
  };

  const handleFeatureClick = (targetPath: string) => {
    if (!isAuthenticated) {
      navigate("/login", { state: { from: { pathname: targetPath } } });
    } else {
      navigate(targetPath);
    }
  };

  return (
    <div className="relative space-y-16 py-6 max-w-6xl mx-auto">
      {/* Sacred Tree Living Background Animation (Matches NyayAI dark ethereal aesthetic) */}
      <SacredTreeBackground growthDuration={4000} scale={1.22} treeOpacity={0.35} />

      {/* 1. HERO SECTION (Solid crisp white text & glowing neon accent, matching NyayAI) */}
      <section className="relative z-10 text-center space-y-6 pt-6 max-w-4xl mx-auto">
        {/* Ministry Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 text-xs font-semibold shadow-md backdrop-blur-md">
          <Award className="w-4 h-4 text-emerald-400" />
          <span>Ministry of Ayush · Legal & Regulatory Intelligence</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl lg:text-6xl font-black tracking-tight text-white leading-[1.15]">
          Authoritative AI Intelligence for{" "}
          <span className="bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent drop-shadow-[0_0_35px_rgba(52,211,153,0.65)]">
            Ayurveda & Herbal IPR
          </span>{" "}
          & Regulatory Compliance
        </h1>

        {/* Hero Subtitle */}
        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Accelerate patentability clearance, streamline ABS compliance, and navigate AYUSH regulatory licensing with source-verified legal intelligence.
        </p>

        {/* Action Button with Option 1B: Radial Center-Out Fill */}
        <div className="flex items-center justify-center pt-2">
          <Button
            size="lg"
            onClick={() => handleFeatureClick("/chat")}
            className="group relative overflow-hidden h-12 px-8 rounded-xl bg-emerald-700 text-white font-semibold text-sm shadow-md shadow-emerald-700/25 hover:shadow-xl hover:shadow-teal-600/30 hover:-translate-y-0.5 transition-all duration-500 gap-2 w-full sm:w-auto cursor-pointer border border-emerald-600/40"
          >
            {/* 1B: Radial Expanding Fluid Fill from Center */}
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400/90 via-emerald-500/90 to-teal-500/90 group-hover:w-[420px] group-hover:h-[420px] transition-all duration-700 ease-out pointer-events-none" />

            {/* Foreground Content */}
            <span className="relative z-10 flex items-center gap-2">
              <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform duration-300" />
              <span>{isAuthenticated ? "Launch AI Consultation" : "Get Started"}</span>
              <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
            </span>
          </Button>
        </div>
      </section>

      {/* 2. CORE MODULES GRID (Interactive Emerging Cards with Frosted Glass Over Roots) */}
      <section className="relative z-10 space-y-6">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            Core IP & Regulatory Decision Modules
          </h2>
          <p className="text-xs sm:text-sm text-slate-300">
            Engineered for AYUSH innovators, manufacturers, and researchers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Conversational Product Classification */}
          <div
            onClick={() => handleFeatureClick("/chat")}
            className="group relative p-6 rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-800 hover:border-emerald-500/80 shadow-lg hover:shadow-2xl hover:shadow-emerald-950/40 transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] cursor-pointer flex flex-col justify-between overflow-hidden text-white"
          >
            {/* Top accent light on hover */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-950/80 text-emerald-400 border border-emerald-800/80 flex items-center justify-center group-hover:scale-110 group-hover:bg-emerald-900/80 transition-all duration-300 shadow-xs">
                <Layers className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                  Conversational Product Diagnostic
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  The Assistant diagnoses your formulation to classify it under 6 statutory categories (Classical ASU, Proprietary ASU, New Drug 158B, Phytopharmaceutical, Aahara, or Cosmetic).
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-5 pt-3 border-t border-slate-800 space-y-2.5">
              <div className="flex flex-wrap gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Form 25-D
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  FSSAI 2022
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  Rule 158B
                </span>
              </div>
              <div className="flex items-center text-xs font-bold text-emerald-400 transform translate-y-1.5 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Launch Diagnostic Module</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* Card 2: Section 3(p) Patentability & Prior Art Clearance */}
          <div
            onClick={() => handleFeatureClick("/chat?intent=PATENTABILITY")}
            className="group relative p-6 rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-800 hover:border-amber-500/80 shadow-lg hover:shadow-2xl hover:shadow-amber-950/40 transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] cursor-pointer flex flex-col justify-between overflow-hidden text-white"
          >
            {/* Top accent light on hover */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-amber-400 to-amber-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-950/80 text-amber-400 border border-amber-800/80 flex items-center justify-center group-hover:scale-110 group-hover:bg-amber-900/80 transition-all duration-300 shadow-xs">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-white group-hover:text-amber-300 transition-colors">
                  Section 3(p) Patentability & Clearance
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Evaluate formulation patentability under Section 3(p) of the Indian Patents Act, cross-reference TKDL traditional knowledge prior art, and identify non-obvious synergistic innovations.
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-5 pt-3 border-t border-slate-800 space-y-2.5">
              <div className="flex flex-wrap gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-amber-950 text-amber-300 border border-amber-800">
                  Section 3(p)
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  TKDL Prior Art
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  Synergistic Claims
                </span>
              </div>
              <div className="flex items-center text-xs font-bold text-amber-400 transform translate-y-1.5 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Check Patentability</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* Card 3: RAG-Grounded Legal Consultation Assistant */}
          <div
            onClick={() => handleFeatureClick("/chat")}
            className="group relative p-6 rounded-2xl bg-slate-900/80 backdrop-blur-md border border-slate-800 hover:border-teal-500/80 shadow-lg hover:shadow-2xl hover:shadow-teal-950/40 transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.01] cursor-pointer flex flex-col justify-between overflow-hidden text-white"
          >
            {/* Top accent light on hover */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-teal-500 via-emerald-400 to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

            <div className="space-y-4">
              <div className="w-12 h-12 rounded-xl bg-teal-950/80 text-teal-400 border border-teal-800/80 flex items-center justify-center group-hover:scale-110 group-hover:bg-teal-900/80 transition-all duration-300 shadow-xs">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-white group-hover:text-teal-300 transition-colors">
                  RAG Consultation with Grounded Citations
                </h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Ask intricate legal questions and receive answers cross-checked against canonical vector collections with verified source links to Official Gazettes.
                </p>
              </div>
            </div>

            {/* Emerging Details & Tags Drawer */}
            <div className="mt-5 pt-3 border-t border-slate-800 space-y-2.5">
              <div className="flex flex-wrap gap-1.5 opacity-80 group-hover:opacity-100 transition-opacity duration-300">
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-teal-950 text-teal-300 border border-teal-800">
                  Patents Act § 3(p)
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  TKDL Prior Art
                </span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  Zero Hallucination
                </span>
              </div>
              <div className="flex items-center text-xs font-bold text-teal-400 transform translate-y-1.5 opacity-0 group-hover:translate-y-0 group-hover:opacity-100 transition-all duration-300 gap-1.5">
                <span>Ask Legal Query</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. TRUST & SECURITY SECTION */}
      <section ref={trustSectionRef} className="relative z-10 bg-slate-900/90 border border-slate-800 text-white p-8 sm:p-12 rounded-3xl space-y-8 shadow-2xl backdrop-blur-md">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-950/90 text-emerald-300 border border-emerald-500/50 text-xs font-bold shadow-md">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Institutional Trust Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight" style={{ color: "#ffffff" }}>
            Built for Legal & Regulatory Rigor
          </h2>
          <p className="text-sm sm:text-base text-white font-medium leading-relaxed" style={{ color: "#ffffff" }}>
            Adhering strictly to statutory provisions for traditional knowledge safeguarding.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8 text-center">
          {/* Card 1 */}
          <div
            onMouseEnter={() => handleRetrigger(1)}
            className="group relative space-y-4 p-7 sm:p-9 rounded-3xl bg-slate-800/50 border border-slate-700/60 hover:border-emerald-500/80 hover:bg-slate-800/90 hover:-translate-y-2.5 hover:scale-[1.02] hover:shadow-2xl hover:shadow-emerald-950/60 transition-all duration-500 ease-out cursor-pointer overflow-hidden"
            title="Hover to replay output"
          >
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-12 -right-12 w-36 h-36 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/25 transition-all duration-500 pointer-events-none" />

            {/* Centered Icon */}
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-500/40 transition-all duration-300 shadow-inner">
              <ShieldCheck className="w-7 h-7" />
            </div>

            <h3 className="text-base font-bold text-white tracking-tight">
              Zero Hallucination Grounding
            </h3>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed min-h-[5rem] sm:min-h-[5.5rem] flex items-center justify-center">
              <StreamingTypewriter
                text="Every sentence in consultations is grounded in official gazettes and statutory provisions. Unsupported citations are filtered."
                isActive={trustInView}
                delay={200}
                speed={110}
                triggerKey={cardTriggers[1]}
              />
            </p>
          </div>

          {/* Card 2 */}
          <div
            onMouseEnter={() => handleRetrigger(2)}
            className="group relative space-y-4 p-7 sm:p-9 rounded-3xl bg-slate-800/50 border border-slate-700/60 hover:border-emerald-500/80 hover:bg-slate-800/90 hover:-translate-y-2.5 hover:scale-[1.02] hover:shadow-2xl hover:shadow-emerald-950/60 transition-all duration-500 ease-out cursor-pointer overflow-hidden"
            title="Hover to replay output"
          >
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-12 -right-12 w-36 h-36 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/25 transition-all duration-500 pointer-events-none" />

            {/* Centered Icon */}
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-500/40 transition-all duration-300 shadow-inner">
              <Lock className="w-7 h-7" />
            </div>

            <h3 className="text-base font-bold text-white tracking-tight">
              DPDP-Compliant & Confidential
            </h3>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed min-h-[5rem] sm:min-h-[5.5rem] flex items-center justify-center">
              <StreamingTypewriter
                text="Proprietary formulation data is anonymized before AI processing. Consultation sessions are cryptographically logged for auditability."
                isActive={trustInView}
                delay={500}
                speed={110}
                triggerKey={cardTriggers[2]}
              />
            </p>
          </div>

          {/* Card 3 */}
          <div
            onMouseEnter={() => handleRetrigger(3)}
            className="group relative space-y-4 p-7 sm:p-9 rounded-3xl bg-slate-800/50 border border-slate-700/60 hover:border-emerald-500/80 hover:bg-slate-800/90 hover:-translate-y-2.5 hover:scale-[1.02] hover:shadow-2xl hover:shadow-emerald-950/60 transition-all duration-500 ease-out cursor-pointer overflow-hidden"
            title="Hover to replay output"
          >
            {/* Top emerging accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Ambient background glow aura */}
            <div className="absolute -bottom-12 -right-12 w-36 h-36 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/25 transition-all duration-500 pointer-events-none" />

            {/* Centered Icon */}
            <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto group-hover:scale-110 group-hover:bg-emerald-500/20 group-hover:border-emerald-500/40 transition-all duration-300 shadow-inner">
              <Globe className="w-7 h-7" />
            </div>

            <h3 className="text-base font-bold text-white tracking-tight">
              Human Expert Escalation Desk
            </h3>

            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed min-h-[5rem] sm:min-h-[5.5rem] flex items-center justify-center">
              <StreamingTypewriter
                text="Complex queries or low-confidence determinations can be escalated directly to IP Facilitators for institutional review."
                isActive={trustInView}
                delay={800}
                speed={110}
                triggerKey={cardTriggers[3]}
              />
            </p>
          </div>
        </div>
      </section>

      {/* 4. FINAL CALL TO ACTION */}
      <section className="relative z-10 text-center space-y-4 py-12 max-w-2xl mx-auto">
        <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight" style={{ color: "#ffffff" }}>
          Ready to Accelerate Your Ayurvedic Innovation?
        </h2>
        <p className="text-sm sm:text-base text-white font-medium leading-relaxed max-w-xl mx-auto" style={{ color: "#ffffff" }}>
          Create an account to access the complete suite of IPR, ABS, and Regulatory decision support tools.
        </p>
        <div className="pt-4">
          <Button
            size="lg"
            onClick={() => navigate(isAuthenticated ? "/chat" : "/login")}
            className="group relative overflow-hidden h-12 px-8 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold text-sm shadow-lg shadow-emerald-900/40 hover:shadow-emerald-500/30 hover:-translate-y-0.5 transition-all duration-300 gap-2 cursor-pointer border border-emerald-400/30"
          >
            {/* 1B: Radial Expanding Fluid Fill from Center */}
            <span className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0 h-0 rounded-full bg-gradient-to-r from-teal-400/90 via-emerald-500/90 to-teal-500/90 group-hover:w-[480px] group-hover:h-[480px] transition-all duration-700 ease-out pointer-events-none" />

            {/* Foreground Content */}
            <span className="relative z-10 flex items-center gap-2">
              <Sparkles className="w-4 h-4 group-hover:rotate-12 transition-transform duration-300" />
              <span>{isAuthenticated ? "Go to Consultation Portal" : "Create Account & Start Consultation"}</span>
              <ArrowRight className="w-4 h-4 opacity-80 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
            </span>
          </Button>
        </div>
      </section>
    </div>
  );
};
