import { api } from "./apiClient";
import { User, Role } from "@/types";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
  role?: Role;
  organization?: string;
  language?: string;
}

export interface TokenResult {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export const authService = {
  login: async (payload: LoginPayload): Promise<TokenResult> => {
    return await api.post<TokenResult>("/api/v1/auth/login", payload);
  },

  register: async (payload: RegisterPayload): Promise<User> => {
    return await api.post<User>("/api/v1/auth/register", payload);
  },

  getMe: async (): Promise<User> => {
    return await api.get<User>("/api/v1/users/me");
  },
};
