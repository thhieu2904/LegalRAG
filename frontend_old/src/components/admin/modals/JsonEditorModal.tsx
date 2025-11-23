/**
 * JSON Editor Modal Component
 * ===========================
 *
 * Modal với Monaco Editor (VSCode engine) để edit JSON documents.
 * Pattern tương tự QuestionModals với confirmation flow.
 */

import React, { useState, useEffect, useRef } from "react";
import Editor from "@monaco-editor/react";
import { Button } from "../../ui/button";
import { X, AlertCircle, CheckCircle } from "lucide-react";
import type { editor } from "monaco-editor";

interface JsonEditorModalProps {
  isOpen: boolean;
  onClose: () => void;
  collection: string;
  docId: string;
  initialData: Record<string, unknown>;
  onSave: (
    data: Record<string, unknown>,
    triggerRebuild: boolean
  ) => Promise<void>;
}

export const JsonEditorModal: React.FC<JsonEditorModalProps> = ({
  isOpen,
  onClose,
  collection,
  docId,
  initialData,
  onSave,
}) => {
  const [jsonContent, setJsonContent] = useState<string>("");
  const [isValid, setIsValid] = useState(true);
  const [validationError, setValidationError] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [pendingRebuild, setPendingRebuild] = useState(false);
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);

  // Initialize editor content
  useEffect(() => {
    if (isOpen && initialData) {
      setJsonContent(JSON.stringify(initialData, null, 2));
      setIsValid(true);
      setValidationError("");
    }
  }, [isOpen, initialData]);

  // Validate JSON on change
  const handleEditorChange = (value: string | undefined) => {
    if (!value) {
      setJsonContent("");
      setIsValid(false);
      setValidationError("JSON content cannot be empty");
      return;
    }

    setJsonContent(value);

    try {
      JSON.parse(value);
      setIsValid(true);
      setValidationError("");
    } catch (error) {
      setIsValid(false);
      setValidationError(
        error instanceof Error ? error.message : "Invalid JSON syntax"
      );
    }
  };

  // Handle editor mount
  const handleEditorDidMount = (monacoEditor: editor.IStandaloneCodeEditor) => {
    editorRef.current = monacoEditor;
    // Format on mount
    monacoEditor.getAction("editor.action.formatDocument")?.run();
  };

  // Handle save click - show confirmation modal
  const handleSaveClick = (withRebuild: boolean) => {
    if (!isValid) {
      alert("Please fix JSON errors before saving");
      return;
    }

    setPendingRebuild(withRebuild);
    setShowConfirmModal(true);
  };

  // Confirm and execute save
  const handleConfirmSave = async () => {
    setShowConfirmModal(false);

    try {
      setIsSaving(true);
      const parsedData = JSON.parse(jsonContent);
      await onSave(parsedData, pendingRebuild);

      // Only close if NOT rebuilding (parent will show progress modal)
      if (!pendingRebuild) {
        onClose();
      } else {
        // Delay close to allow progress modal to open
        setTimeout(() => {
          onClose();
        }, 500);
      }
    } catch (error) {
      console.error("Save error:", error);
      alert(
        `Save failed: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Main Editor Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="bg-white rounded-lg shadow-xl w-[90vw] h-[85vh] max-w-6xl flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Edit JSON Document
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {collection} / {docId}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isSaving}
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Validation Status */}
          <div className="px-4 py-2 border-b bg-gray-50">
            {isValid ? (
              <div className="flex items-center gap-2 text-green-600 text-sm">
                <CheckCircle className="w-4 h-4" />
                <span>Valid JSON ✓</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-red-600 text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          {/* Monaco Editor */}
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              defaultLanguage="json"
              value={jsonContent}
              onChange={handleEditorChange}
              onMount={handleEditorDidMount}
              theme="vs-light"
              options={{
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                fontSize: 14,
                lineNumbers: "on",
                renderWhitespace: "selection",
                automaticLayout: true,
                formatOnPaste: true,
                formatOnType: true,
                tabSize: 2,
              }}
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between p-4 border-t bg-gray-50">
            <div className="text-sm text-gray-500">
              💡 Tip: Ctrl+Shift+F to format JSON
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={onClose} disabled={isSaving}>
                Cancel
              </Button>
              <Button
                variant="outline"
                onClick={() => handleSaveClick(false)}
                disabled={!isValid || isSaving}
              >
                💾 Save Only
              </Button>
              <Button
                onClick={() => handleSaveClick(true)}
                disabled={!isValid || isSaving}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isSaving ? "Saving..." : "💾 Save & Rebuild"}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70">
          <div className="bg-white rounded-lg shadow-2xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Confirm Save
            </h3>
            <p className="text-gray-600 mb-6">
              {pendingRebuild ? (
                <>
                  Save changes and <strong>rebuild cache</strong> for{" "}
                  <code className="bg-gray-100 px-1 py-0.5 rounded">
                    {collection}/{docId}
                  </code>
                  ?
                  <br />
                  <br />
                  <span className="text-sm text-yellow-700">
                    ⚠️ Rebuild will take 5-10 seconds
                  </span>
                </>
              ) : (
                <>
                  Save changes <strong>without rebuilding cache</strong>?
                  <br />
                  <br />
                  <span className="text-sm text-gray-500">
                    You can rebuild manually later from Database tab
                  </span>
                </>
              )}
            </p>
            <div className="flex justify-end gap-3">
              <Button
                variant="outline"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConfirmSave}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {pendingRebuild ? "Save & Rebuild" : "Save Only"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
