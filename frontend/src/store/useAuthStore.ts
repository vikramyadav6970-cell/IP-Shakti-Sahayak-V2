import { create } from "zustand";
import { User, Role } from "@/types";
import { useChatStore } from "./useChatStore";

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setToken: (token: string) => void;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  hasRole: (roles: Role[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem("ip_sakti_token"),
  isAuthenticated: Boolean(localStorage.getItem("ip_sakti_token")),
  isLoading: false,

  setToken: (token: string) => {
    localStorage.setItem("ip_sakti_token", token);
    set({ token, isAuthenticated: true });
  },

  setAuth: (user: User, token: string) => {
    localStorage.setItem("ip_sakti_token", token);
    set({ user, token, isAuthenticated: true, isLoading: false });
    // Fresh chat session on login — will only save to database once user enters a message
    useChatStore.getState().startNewConsultation();
  },

  clearAuth: () => {
    localStorage.removeItem("ip_sakti_token");
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    // Clear chat session on logout
    useChatStore.getState().startNewConsultation();
  },

  hasRole: (roles: Role[]) => {
    const { user } = get();
    if (!user) return false;
    return roles.includes(user.role);
  },
}));
