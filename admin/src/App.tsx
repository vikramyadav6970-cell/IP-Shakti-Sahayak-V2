import React, { useEffect } from "react";
import { useAdminAuthStore } from "./store/useAdminAuthStore";
import { AdminLoginPage } from "./app/AdminLoginPage";
import { AdminDashboardPage } from "./app/AdminDashboardPage";
import { adminService } from "./services/adminService";

export const App: React.FC = () => {
  const { isAuthenticated, setAuth, clearAuth } = useAdminAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("ip_sakti_admin_token");
    if (token) {
      if (token === "mock-admin-token") {
        setAuth(
          {
            id: "admin-preview-001",
            name: "Rajesh Verma (Admin)",
            email: "admin@ayush.gov.in",
            role: "ADMIN",
            organization: "Ministry of Ayush",
          },
          token
        );
        return;
      }
      adminService
        .getMe()
        .then((user) => {
          if (user.role === "ADMIN" || user.role === "IP_FACILITATOR" || user.role === "CONTENT_MANAGER") {
            setAuth(user, token);
          } else {
            clearAuth();
          }
        })
        .catch(() => {
          clearAuth();
        });
    }
  }, []);

  if (!isAuthenticated) {
    return <AdminLoginPage onLoginSuccess={() => {}} />;
  }

  return <AdminDashboardPage />;
};

export default App;
