import React from "react";
import { Globe, ArrowRight, ShieldAlert } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useJurisdiction } from "@/store/useJurisdictionStore";

interface JurisdictionOutGuardrailProps {
  detectedJurisdiction: "INDIA" | "INTERNATIONAL" | string;
  query: string;
  onSwitchAndRetry: () => void;
}

export const JurisdictionOutGuardrail: React.FC<JurisdictionOutGuardrailProps> = ({
  detectedJurisdiction,
  query,
  onSwitchAndRetry,
}) => {
  const { primary, setPrimary } = useJurisdiction();
  const targetMode = primary === "INDIA" ? "INTERNATIONAL" : "INDIA";

  const handleSwitch = () => {
    setPrimary(targetMode);
    onSwitchAndRetry();
  };

  return (
    <Card className="border-amber-400 dark:border-amber-600 bg-amber-50/40 dark:bg-amber-950/20 my-3">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300">
          <ShieldAlert className="w-5 h-5 text-amber-600" />
          <CardTitle className="text-sm font-semibold">
            Jurisdiction Out-of-Scope Guardrail Triggered
          </CardTitle>
        </div>
        <CardDescription className="text-xs text-slate-600 dark:text-slate-300">
          Your current consultation is set to{" "}
          <strong>{primary === "INDIA" ? "Indian Law (Patents Act / BDA / FSSAI)" : "International Treaties (TRIPS / Nagoya / WIPO)"}</strong>
          , but your query appears to pertain to{" "}
          <strong>{detectedJurisdiction}</strong>.
        </CardDescription>
      </CardHeader>
      <CardContent className="text-xs text-slate-500 py-1">
        <p className="italic">"{query}"</p>
      </CardContent>
      <CardFooter className="pt-2">
        <Button
          size="sm"
          onClick={handleSwitch}
          className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold gap-1.5"
        >
          <Globe className="w-3.5 h-3.5" />
          Switch to {targetMode === "INDIA" ? "Indian Law" : "International Law"} & Consult
          <ArrowRight className="w-3.5 h-3.5" />
        </Button>
      </CardFooter>
    </Card>
  );
};
