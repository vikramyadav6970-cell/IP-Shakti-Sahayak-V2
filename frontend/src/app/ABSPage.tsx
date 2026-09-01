import React, { useState } from "react";
import {
  ShieldAlert,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  FileCheck,
  Tag,
  Plus,
  X,
  FileText,
  Loader2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { absService, ABSAssessmentPayload, ABSAssessmentResponse } from "@/services/absService";

export const ABSPage: React.FC = () => {
  const [nationality, setNationality] = useState<"INDIAN" | "FOREIGN" | "INDIAN_WITH_FOREIGN_EQUITY">("INDIAN");
  const [origin, setOrigin] = useState<"INDIA" | "FOREIGN" | "BOTH">("INDIA");
  const [activity, setActivity] = useState<"COMMERCIAL_UTILIZATION" | "RESEARCH" | "IPR_APPLICATION" | "TRANSFER_OF_RESULTS">("COMMERCIAL_UTILIZATION");

  const [resourceInput, setResourceInput] = useState("");
  const [resources, setResources] = useState<string[]>([
    "Withania somnifera (Ashwagandha)",
    "Curcuma longa (Haridra)",
  ]);

  const [isAyushPractitioner, setIsAyushPractitioner] = useState(false);
  const [isCodifiedTK, setIsCodifiedTK] = useState(true);
  const [isTradedCommodity, setIsTradedCommodity] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ABSAssessmentResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleAddResource = () => {
    if (!resourceInput.trim()) return;
    setResources([...resources, resourceInput.trim()]);
    setResourceInput("");
  };

  const handleRemoveResource = (index: number) => {
    setResources(resources.filter((_, i) => i !== index));
  };

  const handleAssess = async () => {
    if (resources.length === 0) {
      setErrorMessage("Please enter at least one biological resource / herbal ingredient.");
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);

    try {
      const payload: ABSAssessmentPayload = {
        entity_nationality: nationality,
        biological_resources: resources,
        resource_origin: origin,
        activity_type: activity,
        is_ayush_practitioner: isAyushPractitioner,
        is_codified_traditional_knowledge: isCodifiedTK,
        is_normally_traded_commodity: isTradedCommodity,
      };

      const res = await absService.assess(payload);
      setResult(res);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to evaluate ABS compliance.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-emerald-600" />
          Access & Benefit Sharing (ABS) Compliance Wizard
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Statutory compliance evaluation under Biological Diversity Act 2002 and Biological Diversity (Amendment) Act 2023.
        </p>
      </div>

      {errorMessage && (
        <div role="alert" className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Input Card */}
      <Card className="shadow-sm border-slate-200 dark:border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg">Step 1: Entity & Biological Resource Profile</CardTitle>
          <CardDescription className="text-xs">
            Identify entity citizenship, biological material origin, and proposed commercial or research utilization.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Nationality & Activity Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Entity Legal Status</label>
              <select
                value={nationality}
                onChange={(e: any) => setNationality(e.target.value)}
                className="w-full h-10 px-3 py-2 text-xs rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="INDIAN">Indian Citizen / 100% Indian Entity</option>
                <option value="INDIAN_WITH_FOREIGN_EQUITY">Indian Entity with Foreign Equity/Control</option>
                <option value="FOREIGN">Foreign Citizen / Foreign Corporation</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Resource Geographic Origin</label>
              <select
                value={origin}
                onChange={(e: any) => setOrigin(e.target.value)}
                className="w-full h-10 px-3 py-2 text-xs rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="INDIA">Sourced inside India</option>
                <option value="FOREIGN">Imported from outside India</option>
                <option value="BOTH">Mixed (Domestic & Imported)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Proposed Activity Type</label>
              <select
                value={activity}
                onChange={(e: any) => setActivity(e.target.value)}
                className="w-full h-10 px-3 py-2 text-xs rounded-md border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="COMMERCIAL_UTILIZATION">Commercial Utilization / Manufacturing</option>
                <option value="RESEARCH">Scientific / Phytochemical Research</option>
                <option value="IPR_APPLICATION">Patent / IPR Application Filing</option>
                <option value="TRANSFER_OF_RESULTS">Transfer of Research Results Abroad</option>
              </select>
            </div>
          </div>

          {/* Biological Resources Tags Input */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300">Biological Resources / Botanical Species</label>
            <div className="flex gap-2">
              <Input
                value={resourceInput}
                onChange={(e) => setResourceInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddResource())}
                placeholder="e.g. Withania somnifera (Ashwagandha)"
              />
              <Button type="button" onClick={handleAddResource} variant="outline" size="sm">
                <Plus className="w-4 h-4 mr-1" /> Add
              </Button>
            </div>

            <div className="flex flex-wrap gap-1.5 pt-1">
              {resources.map((res, idx) => (
                <Badge key={idx} variant="secondary" className="gap-1 text-xs py-1 px-2.5">
                  <Tag className="w-3 h-3 text-emerald-600" />
                  {res}
                  <button type="button" onClick={() => handleRemoveResource(idx)} className="hover:text-destructive ml-1">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>

          {/* Exemption & Special Category Checkboxes */}
          <div className="space-y-3 pt-2 border-t border-slate-100 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider block">
              2023 Amendment Exemptions & Conditions
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isAyushPractitioner}
                  onChange={(e) => setIsAyushPractitioner(e.target.checked)}
                  className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Registered AYUSH Practitioner (qualifies for Section 7 fee exemption under 2023 Act)</span>
              </label>

              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isCodifiedTK}
                  onChange={(e) => setIsCodifiedTK(e.target.checked)}
                  className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Utilizing Codified Traditional Knowledge (listed in First Schedule texts)</span>
              </label>

              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isTradedCommodity}
                  onChange={(e) => setIsTradedCommodity(e.target.checked)}
                  className="mt-0.5 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                />
                <span>Traded purely as agricultural commodity (Section 40 exemption)</span>
              </label>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-end pt-2">
          <Button
            onClick={handleAssess}
            disabled={isLoading || resources.length === 0}
            className="bg-emerald-700 hover:bg-emerald-800 text-white font-medium gap-1.5"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Evaluate ABS Compliance
          </Button>
        </CardFooter>
      </Card>

      {/* Results View */}
      {result && (
        <Card className="shadow-sm border-slate-200 dark:border-slate-800 p-6 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
                ABS Regulatory Assessment Result
              </span>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white mt-1">
                {result.approving_authority}
              </h2>
            </div>
            <Badge
              className={`text-xs ${
                result.relevance_label === "HIGH"
                  ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border-rose-300"
                  : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border-emerald-300"
              }`}
            >
              {result.relevance_label} RELEVANCE
            </Badge>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <span className="text-xs font-semibold text-slate-500 uppercase">Mandatory Application Form:</span>
              <p className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-emerald-600" />
                {result.form_type || "No Form Required (Exempt)"}
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-1">
              <span className="text-xs font-semibold text-slate-500 uppercase">Benefit Sharing Levy Guideline:</span>
              <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                {result.benefit_sharing_levy}
              </p>
            </div>
          </div>

          {/* Statutory Provisions */}
          <div className="space-y-1.5 pt-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Applicable Statutory Provisions:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {result.statutory_provisions.map((prov, idx) => (
                <Badge key={idx} variant="outline" className="text-xs text-emerald-800 dark:text-emerald-300 border-emerald-200">
                  <FileText className="w-3 h-3 mr-1 text-emerald-600" />
                  {prov}
                </Badge>
              ))}
            </div>
          </div>

          {/* Actionable Next Steps */}
          <div className="space-y-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <span className="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider block">
              Actionable Compliance Next Steps:
            </span>
            <ul className="space-y-1.5">
              {result.next_steps.map((step, idx) => (
                <li key={idx} className="text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        </Card>
      )}
    </div>
  );
};
