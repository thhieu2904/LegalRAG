import React, { useState } from "react";
import { identifillService } from "../../services/identifillService";

export const ServiceTester: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<
    "unknown" | "connected" | "failed"
  >("unknown");
  const [isLoading, setIsLoading] = useState(false);

  const testConnection = async () => {
    setIsLoading(true);
    try {
      const isConnected = await identifillService.testConnection();
      setConnectionStatus(isConnected ? "connected" : "failed");
    } catch (error) {
      setConnectionStatus("failed");
      console.error("Connection test failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "text-green-600";
      case "failed":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case "connected":
        return "✅";
      case "failed":
        return "❌";
      default:
        return "⚪";
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-4">
      <h3 className="text-lg font-semibold mb-4">Service Connection Test</h3>

      <div className="flex items-center space-x-4">
        <button
          onClick={testConnection}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? "Testing..." : "Test Connection"}
        </button>

        <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
          <span>{getStatusIcon()}</span>
          <span>
            Identifill Service:{" "}
            {connectionStatus === "unknown"
              ? "Not tested"
              : connectionStatus === "connected"
              ? "Connected"
              : "Connection Failed"}
          </span>
        </div>
      </div>

      {connectionStatus === "failed" && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-red-700 text-sm">
            Make sure the identifill service is running on port 8002:
          </p>
          <code className="text-xs bg-red-100 p-1 rounded mt-2 block">
            conda activate identifill_env && cd
            "d:\Personal\LegalRAG_OCR\identifill_service" && uvicorn main:app
            --reload --host 0.0.0.0 --port 8002
          </code>
        </div>
      )}
    </div>
  );
};
