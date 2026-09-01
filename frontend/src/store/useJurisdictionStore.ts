import { create } from "zustand";
import { JurisdictionCode } from "@/types";

export type PrimaryJurisdiction = "INDIA" | "INTERNATIONAL";

export interface JurisdictionState {
  primary: PrimaryJurisdiction;
  internationalTarget: JurisdictionCode;
  setPrimary: (primary: PrimaryJurisdiction) => void;
  setInternationalTarget: (target: JurisdictionCode) => void;
  getActiveJurisdiction: () => JurisdictionCode;
}

const STORAGE_KEY_PRIMARY = "ip_sakti_jurisdiction_primary";
const STORAGE_KEY_TARGET = "ip_sakti_jurisdiction_target";

const initialPrimary: PrimaryJurisdiction =
  (localStorage.getItem(STORAGE_KEY_PRIMARY) as PrimaryJurisdiction) || "INDIA";

const initialTarget: JurisdictionCode =
  (localStorage.getItem(STORAGE_KEY_TARGET) as JurisdictionCode) || "USA";

export const useJurisdictionStore = create<JurisdictionState>((set, get) => ({
  primary: initialPrimary,
  internationalTarget: initialTarget,

  setPrimary: (primary: PrimaryJurisdiction) => {
    localStorage.setItem(STORAGE_KEY_PRIMARY, primary);
    set({ primary });
  },

  setInternationalTarget: (internationalTarget: JurisdictionCode) => {
    localStorage.setItem(STORAGE_KEY_TARGET, internationalTarget);
    set({ internationalTarget });
  },

  getActiveJurisdiction: () => {
    const { primary, internationalTarget } = get();
    if (primary === "INDIA") return "INDIA";
    return internationalTarget;
  },
}));

export function useJurisdiction() {
  const primary = useJurisdictionStore((s) => s.primary);
  const internationalTarget = useJurisdictionStore((s) => s.internationalTarget);
  const setPrimary = useJurisdictionStore((s) => s.setPrimary);
  const setInternationalTarget = useJurisdictionStore((s) => s.setInternationalTarget);
  const active = useJurisdictionStore((s) => s.getActiveJurisdiction());

  return {
    primary,
    internationalTarget,
    setPrimary,
    setInternationalTarget,
    active,
    isIndia: primary === "INDIA",
    isInternational: primary === "INTERNATIONAL",
  };
}
