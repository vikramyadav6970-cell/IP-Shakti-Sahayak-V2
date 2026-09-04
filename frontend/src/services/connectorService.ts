/**
 * frontend/src/services/connectorService.ts
 *
 * Client API methods for User-Managed External Connector Credentials (BYOK).
 */

import { apiClient } from "@/services/apiClient";
import { ConnectorInfo, ConnectorTestResult } from "@/types";

export interface ConnectorActionResponse {
  connector_name: string;
  status: string;
  last_tested_at?: string;
  message: string;
}

export const connectorService = {
  async getConnectors(): Promise<ConnectorInfo[]> {
    return apiClient<ConnectorInfo[]>("/api/v1/connectors");
  },

  async testCredentials(
    connectorName: string,
    credentials: Record<string, string>
  ): Promise<ConnectorTestResult> {
    return apiClient<ConnectorTestResult>(`/api/v1/connectors/${connectorName}/test`, {
      method: "POST",
      body: JSON.stringify({ credentials }),
    });
  },

  async connect(
    connectorName: string,
    credentials: Record<string, string>
  ): Promise<ConnectorActionResponse> {
    return apiClient<ConnectorActionResponse>(`/api/v1/connectors/${connectorName}/connect`, {
      method: "POST",
      body: JSON.stringify({ credentials }),
    });
  },

  async disconnect(connectorName: string): Promise<ConnectorActionResponse> {
    return apiClient<ConnectorActionResponse>(`/api/v1/connectors/${connectorName}`, {
      method: "DELETE",
    });
  },

  async retest(connectorName: string): Promise<ConnectorTestResult> {
    return apiClient<ConnectorTestResult>(`/api/v1/connectors/${connectorName}/retest`, {
      method: "POST",
    });
  },
};
