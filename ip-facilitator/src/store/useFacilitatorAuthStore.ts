import { create } from "zustand";
import { User } from "../types";

interface FacilitatorAuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useFacilitatorAuthStore = create<FacilitatorAuthState>((set) => ({
  user: null,
  token: localStorage.getItem("ip_sakti_facilitator_token"),
  isAuthenticated: Boolean(localStorage.getItem("ip_sakti_facilitator_token")),

  setAuth: (user: User, token: string) => {
    localStorage.setItem("ip_sakti_facilitator_token", token);
    set({ user, token, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem("ip_sakti_facilitator_token");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
