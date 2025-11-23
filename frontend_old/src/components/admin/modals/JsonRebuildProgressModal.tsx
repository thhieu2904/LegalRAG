/**
 * JSON Rebuild Progress Modal
 * ============================
 *
 * Shows real-time rebuild progress for JSON document updates.
 * Polls rebuild status endpoint and displays progress with stages.
 */

import React, { useEffect, useState } from "react";
import { X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "../../ui/button";
import { adminAPI } from "../../../api/axios-config";

interface RebuildStatus {
  status: "idle" | "running" | "success" | "error";
  progress: number;
  message: string;
  scope?: string;
  collection?: string;
  doc_id?: string;
  started_at?: string;
  completed_at?: string;
  error?: string;
  warning?: string; // Backend warning message
}

interface JsonRebuildProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  collection: string;
  docId: string;
}

export const JsonRebuildProgressModal: React.FC<
  JsonRebuildProgressModalProps
> = ({ isOpen, onClose, collection, docId }) => {
  const [status, setStatus] = useState<RebuildStatus>({
    status: "idle",
    progress: 0,
    message: "Initializing rebuild...",
  });

  const [startTime, setStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);

  // Poll rebuild status
  useEffect(() => {
    if (!isOpen) return;

    setStartTime(new Date());

    const pollStatus = async () => {
      try {
        const response = await adminAPI.get(
          `/api/collections/${collection}/documents/${docId}/json/rebuild/status`
        );

        // Backend returns: { success: true, data: { status, progress, ... } }
        // Extract the actual status from nested data
        const statusData = response.data?.data || response.data;
        setStatus(statusData);

        // Stop polling if completed or error
        if (statusData.status === "success" || statusData.status === "error") {
          clearInterval(pollInterval);
        }
      } catch (error) {
        console.error("Error polling rebuild status:", error);
        // Continue polling even on error (status endpoint might not be ready yet)
      }
    };

    // Poll immediately and then every 500ms
    pollStatus();
    const pollInterval = setInterval(pollStatus, 500);

    return () => {
      clearInterval(pollInterval);
    };
  }, [isOpen, collection, docId]);

  // Update elapsed time
  useEffect(() => {
    if (!isOpen || !startTime) return;

    // Stop timer if rebuild completed or failed
    if (status.status === "success" || status.status === "error") {
      return;
    }

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime.getTime()) / 1000);
      setElapsedTime(elapsed);
    }, 100);

    return () => clearInterval(interval);
  }, [isOpen, startTime, status.status]); // Add status.status dependency

  const getProgressBarColor = () => {
    if (status.status === "error") return "bg-red-500";
    if (status.status === "success") return "bg-green-500";
    return "bg-blue-500";
  };

  const getStatusIcon = () => {
    if (status.status === "error") {
      return <AlertCircle className="w-6 h-6 text-red-500" />;
    }
    if (status.status === "success") {
      return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
    return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
  };

  const getStageMessage = () => {
    const progress = status.progress || 0;

    if (progress < 20) return "🔍 Validating JSON structure...";
    if (progress < 40) return "💾 Creating backup...";
    if (progress < 60) return "📝 Updating document...";
    if (progress < 80) return "🔄 Rebuilding router cache...";
    if (progress < 95) return "🗄️ Rebuilding VectorDB (~30s)...";
    if (progress < 100) return "✅ Finalizing rebuild...";
    return "✅ Completed!";
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/60">
      <div className="bg-white rounded-lg shadow-2xl p-6 max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {status.status === "success"
                  ? "Rebuild Complete"
                  : status.status === "error"
                  ? "Rebuild Failed"
                  : "Rebuilding Document"}
              </h3>
              <p className="text-sm text-gray-500">
                {collection} / {docId}
              </p>
            </div>
          </div>
          {status.status !== "running" && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{status.message || getStageMessage()}</span>
            <span className="font-mono font-medium">
              {Math.round(status.progress || 0)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${getProgressBarColor()}`}
              style={{ width: `${status.progress || 0}%` }}
            />
          </div>
        </div>

        {/* Status Details */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Status:</span>
            <span className="font-medium capitalize">{status.status}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Elapsed Time:</span>
            <span className="font-mono font-medium">{elapsedTime}s</span>
          </div>
          {status.scope && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Scope:</span>
              <span className="font-medium capitalize">{status.scope}</span>
            </div>
          )}
        </div>

        {/* Error Message */}
        {status.status === "error" && status.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800 mb-1">
                  Rebuild Error
                </p>
                <p className="text-sm text-red-700">{status.error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {status.status === "success" && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-2">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div className="w-full">
                <p className="text-sm font-medium text-green-800 mb-1">
                  ✅ Rebuild Complete
                </p>
                <p className="text-sm text-green-700 mb-2">{status.message}</p>

                {status.message?.includes("VectorDB rebuilt") && (
                  <div className="bg-green-100 rounded p-2 mt-2">
                    <p className="text-xs text-green-800 font-medium">
                      🎉 Full rebuild completed!
                    </p>
                    <p className="text-xs text-green-700 mt-1">
                      All changes will now reflect in RAG responses.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          {status.status === "running" ? (
            <Button variant="outline" disabled>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Please wait...
            </Button>
          ) : (
            <Button
              onClick={onClose}
              className={
                status.status === "success"
                  ? "bg-green-600 hover:bg-green-700 text-white"
                  : status.status === "error"
                  ? "bg-red-600 hover:bg-red-700 text-white"
                  : ""
              }
            >
              {status.status === "success" ? "Done" : "Close"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
