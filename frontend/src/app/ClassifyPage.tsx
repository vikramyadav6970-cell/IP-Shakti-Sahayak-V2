import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Layers,
  Sparkles,
  Scale,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Tag,
  Plus,
  X,
  Compass,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { classificationService, ClassificationApiResponse, FormulationPayload } from "@/services/classificationService";
import { ProductCategory, DeclaredIntent } from "@/types";

const INTENT_OPTIONS: { key: DeclaredIntent; label: string; desc: string }[] = [
  { key: "PATENT", label: "Patent Filing & Protection", desc: "Evaluate §3(p) TK exclusions and novel claim strategies" },
  { key: "SELL_BUSINESS", label: "Commercial Manufacturing & Sale", desc: "Form 25-D Ayush license or FSSAI registration" },
  { key: "EXPORT", label: "International Export", desc: "Comply with Nagoya Protocol, TRIPS, and foreign regulatory norms" },
  { key: "AYUSH_APPLICATION", label: "AYUSH Regulatory Approval", desc: "Standard classical or proprietary ASU drug licensing" },
  { key: "RESEARCH", label: "Clinical & Academic Research", desc: "Research trials, phytochemical analysis, and bio-enhancement studies" },
];

export const ClassifyPage: React.FC = () => {
  const navigate = useNavigate();

  // Wizard Step: 1 = Details, 2 = Classification & Reconciliation, 3 = Intent & IP Map
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState("Ashwagandha Synergy Formula");
  const [description, setDescription] = useState("Ayurvedic proprietary formulation combining standardized Withania somnifera with Piper nigrum for enhanced bioavailability.");
  const [ingredientInput, setIngredientInput] = useState("");
  const [ingredients, setIngredients] = useState<string[]>([
    "Withania somnifera (Ashwagandha root extract)",
    "Piper nigrum (Maricha / Black pepper)",
  ]);

  // Checkbox Flags
  const [hasClassicalRef, setHasClassicalRef] = useState(true);
  const [classicalTextName, setClassicalTextName] = useState("Ayurvedic Pharmacopoeia of India");
  const [isStrictClassical, setIsStrictClassical] = useState(false);
  const [hasNovelTech, setHasNovelTech] = useState(true);
  const [isPurifiedFraction, setIsPurifiedFraction] = useState(false);
  const [isFoodSupplement, setIsFoodSupplement] = useState(false);
  const [hasSynthetic, setHasSynthetic] = useState(false);
  const [targetMarket, setTargetMarket] = useState("DOMESTIC");

  // Classification API Result
  const [result, setResult] = useState<ClassificationApiResponse | null>(null);
  const [userSelectedCategory, setUserSelectedCategory] = useState<ProductCategory>("PROPRIETARY_MEDICINE");
  const [selectedIntent, setSelectedIntent] = useState<DeclaredIntent>("PATENT");

  const handleAddIngredient = () => {
    if (!ingredientInput.trim()) return;
    setIngredients([...ingredients, ingredientInput.trim()]);
    setIngredientInput("");
  };

  const handleRemoveIngredient = (index: number) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const handleAnalyze = async () => {
    if (!name.trim() || ingredients.length === 0) {
      setErrorMessage("Please provide a product name and at least one ingredient.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const payload: FormulationPayload = {
        name,
        description,
        ingredients,
        has_classical_text_reference: hasClassicalRef,
        classical_text_name: hasClassicalRef ? classicalTextName : undefined,
        is_strict_classical_recipe: isStrictClassical,
        has_novel_excipients_or_delivery: hasNovelTech,
        is_purified_standardized_fraction: isPurifiedFraction,
        is_food_or_dietary_supplement: isFoodSupplement,
        has_synthetic_additives: hasSynthetic,
        target_market: targetMarket,
        user_selected_category: userSelectedCategory,
      };

      const res = await classificationService.classify(payload);
      setResult(res);
      setUserSelectedCategory(res.category);
      setStep(2);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to analyze formulation.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReconcileCategory = async (newCategory: ProductCategory) => {
    setUserSelectedCategory(newCategory);
    setIsLoading(true);
    try {
      const payload: FormulationPayload = {
        name,
        description,
        ingredients,
        has_classical_text_reference: hasClassicalRef,
        classical_text_name: hasClassicalRef ? classicalTextName : undefined,
        is_strict_classical_recipe: isStrictClassical,
        has_novel_excipients_or_delivery: hasNovelTech,
        is_purified_standardized_fraction: isPurifiedFraction,
        is_food_or_dietary_supplement: isFoodSupplement,
        has_synthetic_additives: hasSynthetic,
        target_market: targetMarket,
        user_selected_category: newCategory,
      };

      const res = await classificationService.classify(payload);
      setResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Reconciliation failed.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartConsultation = () => {
    const classId = result?.id || "";
    navigate(`/chat?q=${encodeURIComponent(`What are the patentability and regulatory requirements for ${name}?`)}&intent=${encodeURIComponent(selectedIntent)}&classId=${encodeURIComponent(classId)}`);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <Layers className="w-6 h-6 text-emerald-600" />
          Product Classification & IP Routing Wizard
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Deterministic categorization under Drugs & Cosmetics Act 1940, FSSAI 2022, and Indian Patent Law §3(p).
        </p>
      </div>

      {/* Stepper Indicator */}
      <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
        <div className={`flex items-center gap-2 text-xs font-semibold ${step >= 1 ? "text-emerald-700 dark:text-emerald-400" : "text-slate-400"}`}>
          <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 flex items-center justify-center text-[10px]">1</span>
          Formulation Details
        </div>
        <div className="w-12 h-0.5 bg-slate-200 dark:bg-slate-700" />
        <div className={`flex items-center gap-2 text-xs font-semibold ${step >= 2 ? "text-emerald-700 dark:text-emerald-400" : "text-slate-400"}`}>
          <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 flex items-center justify-center text-[10px]">2</span>
          Regulatory Category
        </div>
        <div className="w-12 h-0.5 bg-slate-200 dark:bg-slate-700" />
        <div className={`flex items-center gap-2 text-xs font-semibold ${step >= 3 ? "text-emerald-700 dark:text-emerald-400" : "text-slate-400"}`}>
          <span className="w-5 h-5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 flex items-center justify-center text-[10px]">3</span>
          IP Protection Map
        </div>
      </div>

      {errorMessage && (
        <div role="alert" className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1: FORMULATION INPUT */}
      {step === 1 && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800">
          <CardHeader>
            <CardTitle className="text-lg">Step 1: Define Formulation & Ingredients</CardTitle>
            <CardDescription className="text-xs">
              Provide botanical ingredients, classical references, and delivery methods for automated regulatory evaluation.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2 space-y-1.5">
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Product / Formulation Name</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Curcumin Bioactive Synergy Capsule"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Intended Market</label>
                <select
                  value={targetMarket}
                  onChange={(e) => setTargetMarket(e.target.value)}
                  className="w-full h-10 px-3 py-2 text-xs rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="DOMESTIC">Domestic (India)</option>
                  <option value="EXPORT">Export / International</option>
                  <option value="BOTH">Domestic & Export</option>
                </select>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Description & Therapeutic Purpose</label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe indication, vehicle, formulation process..."
                className="w-full p-2.5 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Ingredients Tags Input */}
            <div className="space-y-2">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Herbal & Botanical Ingredients</label>
              <div className="flex gap-2">
                <Input
                  value={ingredientInput}
                  onChange={(e) => setIngredientInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddIngredient())}
                  placeholder="e.g. Curcuma longa (Haridra)"
                />
                <Button type="button" onClick={handleAddIngredient} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-1" /> Add
                </Button>
              </div>

              <div className="flex flex-wrap gap-1.5 pt-1">
                {ingredients.map((ing, idx) => (
                  <Badge key={idx} variant="secondary" className="gap-1 text-xs py-1 px-2.5">
                    <Tag className="w-3 h-3 text-emerald-600" />
                    {ing}
                    <button type="button" onClick={() => handleRemoveIngredient(idx)} className="hover:text-destructive ml-1">
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>

            {/* Regulatory Characteristics Checkboxes */}
            <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
              <span className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider block">
                Statutory Characteristics
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="space-y-2">
                  <label className="flex items-start gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={hasClassicalRef}
                      onChange={(e) => setHasClassicalRef(e.target.checked)}
                      className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                    />
                    <span>Referenced in Classical First Schedule Texts (AFI, Charaka, etc.)</span>
                  </label>

                  {hasClassicalRef && (
                    <Input
                      value={classicalTextName}
                      onChange={(e) => setClassicalTextName(e.target.value)}
                      placeholder="Classical Text Name (e.g. Ayurvedic Formulary of India)"
                      className="text-xs h-8 ml-5 w-[90%]"
                    />
                  )}
                </div>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isStrictClassical}
                    onChange={(e) => setIsStrictClassical(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Strict adherence to classical recipe without modifications</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasNovelTech}
                    onChange={(e) => setHasNovelTech(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Novel delivery mechanism / Bioavailability enhancer / Modified ratio</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isPurifiedFraction}
                    onChange={(e) => setIsPurifiedFraction(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Purified/Standardized fraction with min 4 bioactive markers</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={isFoodSupplement}
                    onChange={(e) => setIsFoodSupplement(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Intended as Food, Beverage, or Dietary Supplement (Ayurveda-Aahara)</span>
                </label>

                <label className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasSynthetic}
                    onChange={(e) => setHasSynthetic(e.target.checked)}
                    className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>Contains synthetic vitamins, minerals, or synthetic isolates</span>
                </label>
              </div>
            </div>
          </CardContent>
          <CardFooter className="flex justify-end pt-2">
            <Button
              onClick={handleAnalyze}
              disabled={isLoading || ingredients.length === 0}
              className="bg-emerald-700 hover:bg-emerald-800 text-white font-medium gap-1.5"
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Analyze & Classify Formulation
            </Button>
          </CardFooter>
        </Card>
      )}

      {/* STEP 2: CATEGORY EVALUATION & RECONCILIATION */}
      {step === 2 && result && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800 space-y-4 p-6">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
                Deterministic Rule Evaluation
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                {result.category_name}
              </h2>
            </div>
            <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300">
              {result.category}
            </Badge>
          </div>

          {/* Regulatory Pathway Banner */}
          <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
            <span className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase">
              Mandatory Regulatory Licensing Pathway:
            </span>
            <p className="text-sm text-emerald-800 dark:text-emerald-300 font-medium">
              {result.regulatory_pathway}
            </p>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            <strong>Reasoning:</strong> {result.reasoning}
          </p>

          {/* Fired Rules Audit Trail */}
          <div className="space-y-1.5 pt-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Fired Rules Audit Trail (context.md §2):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {result.rules_fired.map((rf, i) => (
                <Badge key={i} variant="outline" className="text-[11px] font-mono text-slate-600 dark:text-slate-400">
                  <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" />
                  {rf}
                </Badge>
              ))}
            </div>
          </div>

          {/* User Reconciliation Choice */}
          <div className="p-4 rounded-lg border border-amber-300/60 dark:border-amber-700/40 bg-amber-50/30 dark:bg-amber-950/20 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 dark:text-amber-300">
              <Compass className="w-4 h-4 text-amber-600" />
              Category Reconciliation & Override
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              If your commercial intent differs from the rule suggestion, select an alternative to re-evaluate regulatory obligations:
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
              {(["CLASSICAL_MEDICINE", "PROPRIETARY_MEDICINE", "PHYTOPHARMACEUTICAL", "AYURVEDA_AAHARA"] as ProductCategory[]).map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => handleReconcileCategory(cat)}
                  className={`p-2 text-xs rounded-md border text-center transition-all ${
                    result.category === cat
                      ? "border-emerald-600 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-200 font-bold shadow-sm"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 hover:border-slate-300"
                  }`}
                >
                  {cat.replace("_", " ")}
                </button>
              ))}
            </div>
          </div>

          <div className="flex justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button variant="ghost" size="sm" onClick={() => setStep(1)} className="text-xs text-slate-500">
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Formulation
            </Button>
            <Button onClick={() => setStep(3)} className="bg-emerald-700 hover:bg-emerald-800 text-white font-medium text-xs gap-1">
              Confirm Category & View IP Map <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      )}

      {/* STEP 3: INTENT & IP PROTECTION MAP */}
      {step === 3 && result && (
        <div className="space-y-6">
          {/* Intent Selector */}
          <Card className="shadow-sm border-slate-200 dark:border-slate-800 p-5 space-y-3">
            <div className="flex items-center gap-2 font-semibold text-sm text-slate-900 dark:text-white">
              <Scale className="w-4 h-4 text-emerald-600" />
              Declare Primary Commercial / IP Intent
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {INTENT_OPTIONS.map((opt) => (
                <button
                  key={opt.key}
                  type="button"
                  onClick={() => setSelectedIntent(opt.key)}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    selectedIntent === opt.key
                      ? "border-emerald-600 bg-emerald-50/70 dark:bg-emerald-950/50 shadow-sm"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300"
                  }`}
                >
                  <span className="font-semibold text-xs text-slate-900 dark:text-white block">{opt.label}</span>
                  <span className="text-[11px] text-slate-500 block mt-0.5">{opt.desc}</span>
                </button>
              ))}
            </div>
          </Card>

          {/* IP Protection Map Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Patent Card */}
            <Card className="p-4 space-y-2 border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">Patents Act §3(p)</span>
                <Badge
                  variant="outline"
                  className={`text-[10px] ${
                    result.ip_protection_map.patent.eligibility === "EXCLUDED"
                      ? "border-rose-400 text-rose-700 bg-rose-50 dark:bg-rose-950/50"
                      : "border-emerald-400 text-emerald-700 bg-emerald-50 dark:bg-emerald-950/50"
                  }`}
                >
                  {result.ip_protection_map.patent.eligibility}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {result.ip_protection_map.patent.reason}
              </p>
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-emerald-700 dark:text-emerald-400 font-medium">
                Action: {result.ip_protection_map.patent.action}
              </div>
            </Card>

            {/* Trademark Card */}
            <Card className="p-4 space-y-2 border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">Trademark & Brand</span>
                <Badge variant="outline" className="text-[10px] border-emerald-400 text-emerald-700 bg-emerald-50">
                  {result.ip_protection_map.trademark.nice_class}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                Register distinctive proprietary brand name. Generic classical formulations cannot be registered as trademarks.
              </p>
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-emerald-700 dark:text-emerald-400 font-medium">
                Action: {result.ip_protection_map.trademark.action}
              </div>
            </Card>

            {/* ABS Card */}
            <Card className="p-4 space-y-2 border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase">ABS / Biodiversity</span>
                <Badge variant="outline" className="text-[10px] border-amber-400 text-amber-700 bg-amber-50">
                  {result.ip_protection_map.abs.eligibility}
                </Badge>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                {result.ip_protection_map.abs.action}
              </p>
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800 text-[11px] text-amber-700 dark:text-amber-400 font-medium">
                Authority: NBA / State Biodiversity Board
              </div>
            </Card>
          </div>

          {/* Action CTA Box */}
          <Card className="p-5 bg-emerald-900 text-white flex flex-col sm:flex-row items-center justify-between gap-4 shadow-md">
            <div className="space-y-1">
              <h3 className="font-bold text-base flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-300" />
                Launch Consultation with Active Formulation Context
              </h3>
              <p className="text-xs text-emerald-200 max-w-xl">
                The AI assistant will automatically thread this {result.category_name} classification and {selectedIntent} intent into all legal responses.
              </p>
            </div>

            <Button
              size="lg"
              onClick={handleStartConsultation}
              className="bg-white hover:bg-emerald-50 text-emerald-900 font-bold text-xs shrink-0"
            >
              Start AI Consultation <ArrowRight className="w-4 h-4 ml-1.5" />
            </Button>
          </Card>
        </div>
      )}
    </div>
  );
};
