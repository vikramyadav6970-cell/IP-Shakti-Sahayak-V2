import { create } from "zustand";
import { User, Role } from "@/types";
import { useChatStore } from "./useChatStore";

const getStoredUser = (): User | null => {
  try {
    const raw = localStorage.getItem("ip_sakti_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  setToken: (token: string) => void;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;
  initAuth: () => Promise<void>;
  hasRole: (roles: Role[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: getStoredUser(),
  token: localStorage.getItem("ip_sakti_token"),
  isAuthenticated: Boolean(localStorage.getItem("ip_sakti_token")),
  isLoading: false,
  isInitialized: false,

  setToken: (token: string) => {
    localStorage.setItem("ip_sakti_token", token);
    set({ token, isAuthenticated: true });
  },

  setAuth: (user: User, token: string) => {
    localStorage.setItem("ip_sakti_token", token);
    localStorage.setItem("ip_sakti_user", JSON.stringify(user));
    set({ user, token, isAuthenticated: true, isLoading: false, isInitialized: true });
    // Fresh chat session on login — will only save to database once user enters a message
    useChatStore.getState().startNewConsultation();
  },

  clearAuth: () => {
    localStorage.removeItem("ip_sakti_token");
    localStorage.removeItem("ip_sakti_user");
    set({ user: null, token: null, isAuthenticated: false, isLoading: false, isInitialized: true });
    // Clear chat session on logout
    useChatStore.getState().startNewConsultation();
  },

  initAuth: async () => {
    const token = localStorage.getItem("ip_sakti_token");
    if (!token) {
      set({ isInitialized: true, isLoading: false });
      return;
    }
    set({ isLoading: true });
    try {
      const { authService } = await import("@/services/authService");
      const user = await authService.getMe();
      localStorage.setItem("ip_sakti_user", JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false, isInitialized: true });
    } catch (err: any) {
      if (err?.status === 401 || err?.status === 403) {
        get().clearAuth();
      } else {
        set({ isInitialized: true, isLoading: false });
      }
    }
  },

  hasRole: (roles: Role[]) => {
    const { user } = get();
    if (!user) return false;
    return roles.includes(user.role);
  },
}));

