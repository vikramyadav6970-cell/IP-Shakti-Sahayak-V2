import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "@/app/Layout";
import { LandingPage } from "@/app/LandingPage";
import { ChatPage } from "@/app/ChatPage";
import { ABSPage } from "@/app/ABSPage";
import { FacilitatorQueriesPage } from "@/app/FacilitatorQueriesPage";
import { LoginPage } from "@/app/LoginPage";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useAuthStore } from "@/store/useAuthStore";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000,
    },
  },
});

const IndexRoute: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }
  return <LandingPage />;
};

const LoginRoute: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }
  return <LoginPage />;
};

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<IndexRoute />} />
            <Route
              path="chat"
              element={
                <ProtectedRoute>
                  <ChatPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="classify"
              element={<Navigate to="/chat?mode=classify" replace />}
            />
            <Route
              path="abs"
              element={
                <ProtectedRoute>
                  <ABSPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="facilitator-desk"
              element={
                <ProtectedRoute>
                  <FacilitatorQueriesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="my-queries"
              element={<Navigate to="/facilitator-desk" replace />}
            />
            <Route path="login" element={<LoginRoute />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

export default App;
