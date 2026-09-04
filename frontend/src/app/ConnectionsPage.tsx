import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plug,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Key,
  Globe,
  Database,
  Trash2,
  Lock,
  X,
  BookOpen,
} from "lucide-react";
import { connectorService } from "@/services/connectorService";
import { ConnectorInfo, ConnectorTestResult } from "@/types";
import { Button } from "@/components/ui/button";

export const ConnectionsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedConnector, setSelectedConnector] = useState<ConnectorInfo | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [testResult, setTestResult] = useState<ConnectorTestResult | null>(null);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [activeRetestingName, setActiveRetestingName] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Fetch connector statuses
  const { data: connectors = [], isLoading, isError } = useQuery<ConnectorInfo[]>({
    queryKey: ["external-connectors"],
    queryFn: connectorService.getConnectors,
  });

  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: async ({ name, creds }: { name: string; creds: Record<string, string> }) => {
      return connectorService.connect(name, creds);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["external-connectors"] });
      setSelectedConnector(null);
      setFormData({});
      setTestResult(null);
      setActionMessage({ type: "success", text: data.message });
      setTimeout(() => setActionMessage(null), 5000);
    },
    onError: (err: any) => {
      const msg = err?.data?.detail?.error_message || err?.message || "Failed to save connection.";
      setActionMessage({ type: "error", text: msg });
    },
  });

  // Disconnect mutation
  const disconnectMutation = useMutation({
    mutationFn: async (name: string) => {
      return connectorService.disconnect(name);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["external-connectors"] });
      setActionMessage({ type: "success", text: data.message });
      setTimeout(() => setActionMessage(null), 5000);
    },
    onError: (err: any) => {
      setActionMessage({ type: "error", text: err?.message || "Failed to disconnect." });
    },
  });

  const handleOpenConnectModal = (connector: ConnectorInfo) => {
    setSelectedConnector(connector);
    setFormData({});
    setTestResult(null);
  };

  const handleCloseModal = () => {
    setSelectedConnector(null);
    setFormData({});
    setTestResult(null);
    setIsTesting(false);
  };

  const handleInputChange = (fieldName: string, value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    // Reset test result if user changes credentials
    if (testResult) setTestResult(null);
  };

  const handleTestCredentials = async () => {
    if (!selectedConnector) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const res = await connectorService.testCredentials(selectedConnector.name, formData);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({
        success: false,
        error_code: "AUTH_FAILED",
        error_message: err?.message || "Connection verification failed.",
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveConnection = () => {
    if (!selectedConnector) return;
    connectMutation.mutate({ name: selectedConnector.name, creds: formData });
  };

  const handleRetestStored = async (connectorName: string) => {
    setActiveRetestingName(connectorName);
    try {
      const res = await connectorService.retest(connectorName);
      queryClient.invalidateQueries({ queryKey: ["external-connectors"] });
      if (res.success) {
        setActionMessage({ type: "success", text: "Connection verified successfully." });
      } else {
        setActionMessage({
          type: "error",
          text: `Verification failed: ${res.error_message || "Invalid credentials"}`,
        });
      }
      setTimeout(() => setActionMessage(null), 5000);
    } catch (err: any) {
      setActionMessage({ type: "error", text: "Retest error." });
    } finally {
      setActiveRetestingName(null);
    }
  };

  const handleDisconnect = (connectorName: string) => {
    if (window.confirm(`Are you sure you want to disconnect ${connectorName}?`)) {
      disconnectMutation.mutate(connectorName);
    }
  };

  const handleConnectPublic = (connectorName: string) => {
    connectMutation.mutate({ name: connectorName, creds: {} });
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center text-white shadow-sm">
              <Plug className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
              External Integrations & BYOK
            </h1>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl">
            Bring your own API keys for official international patent registries, terminology databases, and commercial IP search platforms. Live lookups in chat will automatically use your authorized credentials.
          </p>
        </div>

        <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
          <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>Encrypted at rest (AES-256 / Fernet)</span>
        </div>
      </div>

      {/* Global Action Message Banner */}
      {actionMessage && (
        <div
          className={`mb-6 p-4 rounded-xl border flex items-center gap-3 transition-all ${
            actionMessage.type === "success"
              ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
              : "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200"
          }`}
        >
          {actionMessage.type === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400 shrink-0" />
          )}
          <span className="text-sm font-medium">{actionMessage.text}</span>
        </div>
      )}

      {/* Write-Only Security Info Banner */}
      <div className="mb-8 p-4 rounded-2xl bg-gradient-to-r from-slate-900 to-slate-800 text-white shadow-md border border-slate-700/50 flex flex-col sm:flex-row items-start sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-9 h-9 rounded-xl bg-white/10 flex items-center justify-center shrink-0 mt-0.5 sm:mt-0">
            <Lock className="w-4 h-4 text-amber-300" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              Write-Only Credential Security
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                DPDP & ISO Aligned
              </span>
            </h3>
            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
              Once saved, secret keys are never returned to the frontend or echoed in logs. Connections are tested in-memory and stored symmetrically encrypted.
            </p>
          </div>
        </div>
      </div>

      {/* Loading & Error States */}
      {isLoading && (
        <div className="p-12 text-center text-slate-500 dark:text-slate-400">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-3 text-emerald-600" />
          <p className="text-sm font-medium">Loading external connectors...</p>
        </div>
      )}

      {isError && (
        <div className="p-8 text-center rounded-2xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900">
          <AlertTriangle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-rose-900 dark:text-rose-200">Unable to load connectors</h3>
          <p className="text-xs text-rose-700 dark:text-rose-400 mt-1">
            Please make sure the backend server is running and accessible.
          </p>
        </div>
      )}

      {/* Connector Grid */}
      {!isLoading && !isError && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {connectors.map((connector) => {
            const isConnected = connector.is_connected && connector.status === "connected";
            const isErrorState = connector.status === "error";

            return (
              <div
                key={connector.name}
                className={`flex flex-col justify-between p-5 rounded-2xl border transition-all duration-300 bg-white dark:bg-slate-900 shadow-sm ${
                  isConnected
                    ? "border-emerald-300 dark:border-emerald-800/80 shadow-emerald-500/5 ring-1 ring-emerald-400/20"
                    : isErrorState
                    ? "border-amber-300 dark:border-amber-800/80"
                    : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700"
                }`}
              >
                <div>
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-white ${
                          isConnected
                            ? "bg-emerald-600 shadow-sm shadow-emerald-600/30"
                            : "bg-slate-700 dark:bg-slate-800"
                        }`}
                      >
                        {connector.name.includes("patentscope") ? (
                          <Globe className="w-5 h-5" />
                        ) : connector.name.includes("pearl") ? (
                          <Database className="w-5 h-5" />
                        ) : connector.name.includes("pubmed") || connector.name.includes("ncbi") ? (
                          <BookOpen className="w-5 h-5" />
                        ) : (
                          <Key className="w-5 h-5" />
                        )}
                      </div>
                      <div>
                        <h2 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">
                          {connector.display_name}
                        </h2>
                        <span className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                          {connector.name}
                        </span>
                      </div>
                    </div>

                    {/* Status Badge */}
                    {isConnected ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        Connected
                      </span>
                    ) : isErrorState ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                        <AlertTriangle className="w-3 h-3" />
                        Error
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        Disconnected
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                    {connector.description}
                  </p>

                  {/* Metadata Chips */}
                  <div className="flex flex-wrap gap-1.5 mb-4">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                      Rate limit: {connector.rate_limit_per_minute}/min
                    </span>
                    {connector.requires_api_key ? (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-teal-50 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                        BYOK Supported
                      </span>
                    ) : (
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                        Free Public Interface
                      </span>
                    )}
                  </div>

                  {/* Error detail if in error state */}
                  {isErrorState && connector.last_error_message && (
                    <div className="mb-4 p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-900 dark:text-amber-200 text-[11px]">
                      <span className="font-semibold block">Last Error:</span>
                      {connector.last_error_message}
                    </div>
                  )}

                  {connector.last_tested_at && (
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 mb-3">
                      Verified: {new Date(connector.last_tested_at).toLocaleString()}
                    </p>
                  )}
                </div>

                {/* Card Actions */}
                <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-2">
                  {isConnected ? (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={activeRetestingName === connector.name}
                        onClick={() => handleRetestStored(connector.name)}
                        className="text-xs h-8 flex items-center gap-1.5"
                      >
                        <RefreshCw
                          className={`w-3.5 h-3.5 ${activeRetestingName === connector.name ? "animate-spin text-emerald-600" : ""}`}
                        />
                        <span>Test</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDisconnect(connector.name)}
                        className="text-xs h-8 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30 flex items-center gap-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Disconnect</span>
                      </Button>
                    </>
                  ) : connector.requires_api_key ? (
                    <Button
                      size="sm"
                      onClick={() => handleOpenConnectModal(connector)}
                      className="w-full text-xs h-8 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center justify-center gap-1.5"
                    >
                      <Key className="w-3.5 h-3.5" />
                      <span>Connect Account</span>
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => handleConnectPublic(connector.name)}
                      className="w-full text-xs h-8 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold flex items-center justify-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Enable Connection</span>
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Dynamic Connect Modal */}
      {selectedConnector && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-xs animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl p-6 relative">
            {/* Close Button */}
            <button
              onClick={handleCloseModal}
              className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Modal Title */}
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-800 flex items-center justify-center text-white shadow-sm">
                <Key className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  Connect {selectedConnector.display_name}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Enter your credentials. They will be validated live before saving.
                </p>
              </div>
            </div>

            {/* Dynamic Fields */}
            <div className="space-y-4 my-5">
              {selectedConnector.credential_fields.map((field) => (
                <div key={field.name} className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    {field.label} {field.required && <span className="text-rose-500">*</span>}
                  </label>
                  <input
                    type={field.field_type === "password" ? "password" : "text"}
                    placeholder={field.placeholder}
                    value={formData[field.name] || ""}
                    onChange={(e) => handleInputChange(field.name, e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl text-xs sm:text-sm bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all font-mono"
                  />
                  {field.help_text && (
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                      {field.help_text}
                    </p>
                  )}
                </div>
              ))}
            </div>

            {/* Test Feedback Area */}
            {testResult && (
              <div
                className={`p-3.5 rounded-xl border text-xs mb-4 flex items-start gap-2.5 ${
                  testResult.success
                    ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200"
                    : "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200"
                }`}
              >
                {testResult.success ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <span className="font-bold block">
                    {testResult.success ? "Verification Succeeded" : `Verification Failed (${testResult.error_code || "ERROR"})`}
                  </span>
                  <span className="text-[11px] mt-0.5 block opacity-90">
                    {testResult.success
                      ? "Your credentials were authenticated with the provider. You can now save this connection."
                      : testResult.error_message || "The provider rejected these credentials. Please verify your inputs."}
                  </span>
                </div>
              </div>
            )}

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button variant="ghost" size="sm" onClick={handleCloseModal}>
                Cancel
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={isTesting}
                onClick={handleTestCredentials}
                className="text-xs font-semibold"
              >
                {isTesting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin mr-1.5" />
                    Testing...
                  </>
                ) : (
                  "Test Connection"
                )}
              </Button>
              <Button
                size="sm"
                disabled={!testResult?.success || connectMutation.isPending}
                onClick={handleSaveConnection}
                className="text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {connectMutation.isPending ? "Saving..." : "Save & Encrypt"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
