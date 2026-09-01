import { create } from "zustand";
import { User } from "../types";

interface AdminAuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
}

export const useAdminAuthStore = create<AdminAuthState>((set) => ({
  user: null,
  token: localStorage.getItem("ip_sakti_admin_token"),
  isAuthenticated: Boolean(localStorage.getItem("ip_sakti_admin_token")),

  setAuth: (user: User, token: string) => {
    localStorage.setItem("ip_sakti_admin_token", token);
    set({ user, token, isAuthenticated: true });
  },

  clearAuth: () => {
    localStorage.removeItem("ip_sakti_admin_token");
    set({ user: null, token: null, isAuthenticated: false });
  },
}));
