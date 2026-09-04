import React, { useEffect } from "react";
import { useFacilitatorAuthStore } from "./store/useFacilitatorAuthStore";
import { FacilitatorLoginPage } from "./app/FacilitatorLoginPage";
import { FacilitatorDashboardPage } from "./app/FacilitatorDashboardPage";
import { facilitatorService } from "./services/facilitatorService";

export const App: React.FC = () => {
  const { isAuthenticated, setAuth, clearAuth } = useFacilitatorAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("ip_sakti_facilitator_token");
    if (token) {
      if (token === "mock-facilitator-token") {
        setAuth(
          {
            id: "fac-preview-001",
            name: "Dr. Ananya Sharma",
            email: "facilitator@ayush.gov.in",
            role: "IP_FACILITATOR",
            organization: "Ministry of Ayush",
          },
          token
        );
        return;
      }
      facilitatorService
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
    return <FacilitatorLoginPage onLoginSuccess={() => {}} />;
  }

  return <FacilitatorDashboardPage />;
};

export default App;
