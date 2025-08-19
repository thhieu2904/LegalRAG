import React, { useState, useEffect } from "react";
import { ChatService, type ContextSummary } from "../../services/chatService";

export const ContextInfoModal: React.FC = () => {
  const [contextSummary, setContextSummary] = useState<ContextSummary | null>(
    null
  );
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const updateInfo = async () => {
      const currentSessionId = ChatService.getCurrentSessionId();
      setSessionId(currentSessionId);

      if (currentSessionId) {
        try {
          const context = await ChatService.getSessionContext(currentSessionId);
          setContextSummary(context);
        } catch (error) {
          console.error("Error fetching context:", error);
        }
      }
    };

    // Update immediately
    updateInfo();

    // 🔧 FIX: Update every 30 seconds instead of 10 (reduce polling)
    const interval = setInterval(updateInfo, 30000);

    return () => clearInterval(interval);
  }, []);

  if (!sessionId) {
    return null; // Không hiển thị gì khi chưa có session
  }

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsModalOpen(true)}
        className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 text-sm flex items-center gap-1"
        title="View Context Info"
      >
        📊 Context
        {contextSummary?.has_active_context && (
          <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
        )}
      </button>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-96 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 bg-gray-50 border-b">
              <h3 className="text-lg font-medium text-gray-900">
                📊 Context Information
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="p-4 space-y-3 overflow-auto max-h-80">
              {/* Session Info */}
              <div className="space-y-2">
                <div className="font-medium text-gray-700">Session</div>
                <div className="text-gray-500 font-mono text-sm break-all">
                  {sessionId?.substring(0, 8)}...
                </div>
              </div>

              {contextSummary && (
                <>
                  <div className="border-t pt-3">
                    <div className="font-medium text-gray-700 mb-2">
                      Active Context
                    </div>
                    <div
                      className={`text-sm px-3 py-2 rounded ${
                        contextSummary.has_active_context
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {contextSummary.has_active_context ? "Yes" : "No"}
                    </div>
                  </div>

                  {contextSummary.has_active_context && (
                    <>
                      {/* Current Collection */}
                      <div className="space-y-2">
                        <div className="font-medium text-gray-700">
                          Collection
                        </div>
                        <div className="text-blue-600 bg-blue-50 px-3 py-2 rounded text-sm">
                          {contextSummary.current_collection_display || "N/A"}
                        </div>
                      </div>

                      {/* Preserved Document */}
                      {contextSummary.preserved_document && (
                        <div className="space-y-2">
                          <div className="font-medium text-gray-700">
                            Document
                          </div>
                          <div className="text-purple-600 bg-purple-50 px-3 py-2 rounded text-sm">
                            {contextSummary.preserved_document}
                          </div>
                        </div>
                      )}

                      {/* Context Age */}
                      <div className="space-y-2">
                        <div className="font-medium text-gray-700">Age</div>
                        <div className="text-orange-600 text-sm">
                          {contextSummary.context_age_minutes === 0
                            ? "Just now"
                            : `${contextSummary.context_age_minutes}m ago`}
                        </div>
                      </div>

                      {/* Confidence Level */}
                      <div className="space-y-2">
                        <div className="font-medium text-gray-700">
                          Confidence
                        </div>
                        <div
                          className={`text-sm px-3 py-2 rounded ${
                            contextSummary.confidence_level > 0.8
                              ? "bg-green-100 text-green-800"
                              : contextSummary.confidence_level > 0.6
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-red-100 text-red-800"
                          }`}
                        >
                          {(contextSummary.confidence_level * 100).toFixed(1)}%
                        </div>
                      </div>

                      {/* Query Count */}
                      <div className="space-y-2">
                        <div className="font-medium text-gray-700">
                          Query Count
                        </div>
                        <div className="text-gray-600 text-sm">
                          {contextSummary.query_count} queries
                        </div>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-gray-50 border-t flex justify-end">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
