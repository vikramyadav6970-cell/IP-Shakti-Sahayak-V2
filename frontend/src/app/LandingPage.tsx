import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  ShieldCheck,
  Globe,
  Lock,
  Award,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useAuthStore } from "@/store/useAuthStore";

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
    <div className="space-y-16 py-6 max-w-6xl mx-auto">
      {/* 1. HERO SECTION */}
      <section className="text-center space-y-6 pt-4 max-w-4xl mx-auto">
        {/* Ministry Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 text-xs font-semibold shadow-xs">
          <Award className="w-4 h-4 text-emerald-600" />
          <span>Ministry of Ayush</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
          Authoritative AI Intelligence for{" "}
          <span className="bg-gradient-to-r from-emerald-700 via-teal-600 to-emerald-800 bg-clip-text text-transparent">
            Ayurveda & Herbal IPR
          </span>{" "}
          & Regulatory Compliance
        </h1>

        {/* Hero Subtitle */}
        <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
          Reconcile traditional Ayurvedic formulations against <strong>Patents Act Section 3(p)</strong>, navigate 
          <strong> Biological Diversity Act (ABS)</strong> approvals with 2023 exemptions, and resolve 
          <strong> AYUSH Drug (Form 25-D) vs FSSAI Ayurveda-Aahara</strong> regulatory pathways with zero hallucination.
        </p>

        {/* Action Button */}
        <div className="flex items-center justify-center pt-2">
          <Button
            size="lg"
            onClick={() => handleFeatureClick("/chat")}
            className="h-12 px-8 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-sm shadow-lg shadow-emerald-700/20 gap-2 w-full sm:w-auto"
          >
            <Sparkles className="w-4 h-4" />
            {isAuthenticated ? "Launch AI Consultation" : "Get Started"}
          </Button>
        </div>
      </section>

      {/* 2. CORE MODULES GRID (3 Focused Columns) */}
      <section className="space-y-6">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Core IP & Regulatory Decision Modules
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Engineered for AYUSH innovators, manufacturers, and researchers.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Conversational Product Classification */}
          <Card className="p-6 border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-400 flex items-center justify-center">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                Conversational Product Diagnostic
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                The Assistant diagnoses your formulation to classify it under 6 statutory categories (Classical ASU, Proprietary ASU, New Drug 158B, Phytopharmaceutical, Aahara, or Cosmetic).
              </p>
            </div>
          </Card>

          {/* Card 2: ABS Compliance Wizard */}
          <Card className="p-6 border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-xl bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-400 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                ABS & Biodiversity Act Compliance
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Determine exact National Biodiversity Authority (NBA) approval requirements (Form I, Form II, Form III) and apply 2023 Amendment Section 7 fee exemptions.
              </p>
            </div>
          </Card>

          {/* Card 3: RAG-Grounded Legal Consultation Assistant */}
          <Card className="p-6 border-slate-200 dark:border-slate-800 shadow-sm hover:border-emerald-500/50 transition-all space-y-3">
            <div className="w-12 h-12 rounded-xl bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                RAG Consultation with Grounded Citations
              </h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask intricate legal questions and receive answers cross-checked against canonical vector collections with verified source links to Official Gazettes.
              </p>
            </div>
          </Card>
        </div>
      </section>

      {/* 3. TRUST & SECURITY SECTION */}
      <section className="bg-slate-900 text-white p-8 sm:p-12 rounded-3xl space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-semibold">
            Institutional Trust Architecture
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold">
            Built for Legal & Regulatory Rigor
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            Adhering strictly to statutory provisions for traditional knowledge safeguarding.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
          <div className="space-y-2 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <ShieldCheck className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-bold">Zero Hallucination Grounding</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Every sentence in consultations is grounded in official gazettes and statutory provisions. Unsupported citations are filtered.
            </p>
          </div>

          <div className="space-y-2 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Lock className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-bold">DPDP-Compliant & Confidential</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Proprietary formulation data is anonymized before AI processing. Consultation sessions are cryptographically logged for auditability.
            </p>
          </div>

          <div className="space-y-2 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Globe className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-sm font-bold">Human Expert Escalation Desk</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Complex queries or low-confidence determinations can be escalated directly to IP Facilitators for institutional review.
            </p>
          </div>
        </div>
      </section>

      {/* 4. FINAL CALL TO ACTION */}
      <section className="text-center space-y-4 py-8 max-w-xl mx-auto">
        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
          Ready to Accelerate Your Ayurvedic Innovation?
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Create an account to access the complete suite of IPR, ABS, and Regulatory decision support tools.
        </p>
        <div className="pt-2">
          <Button
            size="lg"
            onClick={() => navigate(isAuthenticated ? "/chat" : "/login")}
            className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-8 shadow-lg shadow-emerald-700/20 gap-2"
          >
            <Sparkles className="w-4 h-4" />
            {isAuthenticated ? "Go to Consultation Portal" : "Create Account & Start Consultation"}
          </Button>
        </div>
      </section>
    </div>
  );
};
