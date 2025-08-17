import React, { useState } from "react";
import { ChatService, type ContextSummary } from "../services/chatService";
import { ContextStatusBar } from "./ContextStatusBar";

export const ContextDebugComponent: React.FC = () => {
  const [contextSummary, setContextSummary] = useState<ContextSummary | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const addLog = (message: string) => {
    setLogs((prev) => [
      ...prev,
      `${new Date().toLocaleTimeString()}: ${message}`,
    ]);
  };

  const testContextFetch = async () => {
    setIsLoading(true);
    addLog("Starting context fetch test...");

    try {
      // Get current session ID
      const currentSessionId = ChatService.getCurrentSessionId();
      setSessionId(currentSessionId);
      addLog(`Current session ID: ${currentSessionId || "null"}`);

      if (!currentSessionId) {
        addLog(
          "No session ID found - sending a test message to create session"
        );
        const response = await ChatService.sendMessage("Hello test");
        addLog(`Response received: ${response.response.substring(0, 50)}...`);

        const newSessionId = ChatService.getCurrentSessionId();
        setSessionId(newSessionId);
        addLog(`New session ID: ${newSessionId}`);

        if (newSessionId) {
          const context = await ChatService.getSessionContext(newSessionId);
          setContextSummary(context);
          addLog(`Context fetched: ${JSON.stringify(context)}`);
        }
      } else {
        const context = await ChatService.getSessionContext(currentSessionId);
        setContextSummary(context);
        addLog(`Context fetched: ${JSON.stringify(context)}`);
      }
    } catch (error) {
      addLog(`Error: ${error}`);
      console.error("Context fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetContext = async () => {
    if (!sessionId) {
      addLog("No session to reset");
      return;
    }

    setIsLoading(true);
    addLog("Resetting context...");

    try {
      const success = await ChatService.resetSessionContext(sessionId);
      addLog(`Reset success: ${success}`);

      if (success) {
        setContextSummary(null);
        addLog("Context cleared");
      }
    } catch (error) {
      addLog(`Reset error: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
      <h3 className="text-lg font-semibold mb-4">Context Debug Panel</h3>

      <div className="space-y-4">
        <div>
          <strong>Session ID:</strong> {sessionId || "null"}
        </div>

        <div>
          <strong>Context Summary:</strong>
          <pre className="text-xs bg-white p-2 rounded border overflow-auto max-h-32">
            {JSON.stringify(contextSummary, null, 2) || "null"}
          </pre>
        </div>

        <div className="space-x-2">
          <button
            onClick={testContextFetch}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {isLoading ? "Testing..." : "Test Context Fetch"}
          </button>

          <button
            onClick={handleResetContext}
            disabled={isLoading || !sessionId}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            Reset Context
          </button>
        </div>

        <div>
          <strong>Context Status Bar Preview:</strong>
          <ContextStatusBar
            contextSummary={contextSummary}
            isLoading={isLoading}
            onResetContext={handleResetContext}
          />
        </div>

        <div>
          <strong>Logs:</strong>
          <div className="text-xs bg-white p-2 rounded border h-32 overflow-auto">
            {logs.map((log, index) => (
              <div key={index}>{log}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextDebugComponent;
