/**
 * 📄 Document Preview Page
 * Full-page viewer for DOCX and JSON documents
 * Accessible via: /admin/documents/:collection/:docId/preview/:type
 * Layout: ChatHeader + Content (scrollable) + ChatFooter
 */

import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getDocumentPreview } from "../api/document-preview-api";
import type { DocumentPreviewResponse } from "../api/document-preview-api";
import { updateJsonDocument } from "../api/json-documents-api";
import {
  ArrowLeft,
  FileText,
  Download,
  AlertCircle,
  Edit,
  CheckCircle,
  X,
} from "lucide-react";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatFooter } from "../components/chat/ChatFooter";
import { JsonEditorModal } from "../components/admin/modals/JsonEditorModal";
import { JsonRebuildProgressModal } from "../components/admin/modals/JsonRebuildProgressModal";
import "./ChatPage.css"; // Shared layout styles
import "./DocumentPreviewPage.css"; // Page-specific styles

const DocumentPreviewPage: React.FC = () => {
  const { collection, docId, type } = useParams<{
    collection: string;
    docId: string;
    type: "docx" | "json";
  }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewData, setPreviewData] =
    useState<DocumentPreviewResponse | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [showRebuildProgress, setShowRebuildProgress] = useState(false);
  const [notification, setNotification] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const loadPreview = async () => {
    if (!collection || !docId || !type) {
      setError("Missing required parameters");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await getDocumentPreview(collection, docId, type);

      if (!data.success) {
        setError(data.error || "Failed to load document");
      } else {
        setPreviewData(data);
      }
    } catch (err) {
      console.error("Error loading preview:", err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(
        error.response?.data?.detail || "Failed to load document preview"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreview();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collection, docId, type]);

  const handleBack = () => {
    navigate("/admin");
  };

  const handleEditJson = () => {
    setIsEditorOpen(true);
  };

  const handleSaveJson = async (
    data: Record<string, unknown>,
    triggerRebuild: boolean
  ) => {
    if (!collection || !docId) return;

    try {
      await updateJsonDocument(collection, docId, data, triggerRebuild);

      // Show rebuild progress if triggered
      if (triggerRebuild) {
        setShowRebuildProgress(true);
      }

      // Reload preview to show updated content
      await loadPreview();

      // Show success notification
      setNotification({
        type: "success",
        message: `JSON document saved successfully${
          triggerRebuild ? " (Rebuild started)" : ""
        }`,
      });

      // Auto-hide notification after 5 seconds
      setTimeout(() => setNotification(null), 5000);
    } catch (error) {
      console.error("Failed to save JSON:", error);
      throw error; // Let modal handle the error display
    }
  };

  const handleDownload = () => {
    if (!previewData) return;

    if (type === "json" && previewData.data) {
      // Download JSON
      const blob = new Blob([JSON.stringify(previewData.data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = previewData.filename || `${docId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else if (type === "docx" && previewData.html) {
      // Download HTML version
      const blob = new Blob([previewData.html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${docId}.html`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="preview-loading">
          <div className="text-center">
            <div className="loading-spinner mx-auto"></div>
            <p className="text-gray-600">Đang tải nội dung...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="preview-error">
          <div className="error-content">
            <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Lỗi tải tài liệu
            </h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={loadPreview}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Thử lại
            </button>
          </div>
        </div>
      );
    }

    if (!previewData) {
      return (
        <div className="text-center text-gray-600 py-12">
          Không có dữ liệu để hiển thị
        </div>
      );
    }

    // Render DOCX as HTML
    if (type === "docx" && previewData.html) {
      return (
        <div className="docx-preview-container">
          {/* Conversion warnings */}
          {previewData.messages && previewData.messages.length > 0 && (
            <div className="conversion-warning">
              <p className="conversion-warning-text">
                ⚠️ Có {previewData.messages.length} cảnh báo khi chuyển đổi
              </p>
            </div>
          )}

          {/* HTML Content */}
          <div
            className="docx-html-content prose max-w-none"
            dangerouslySetInnerHTML={{ __html: previewData.html }}
          />
        </div>
      );
    }

    // Render JSON with syntax highlighting
    if (type === "json" && previewData.data) {
      return (
        <div className="json-preview-container">
          <pre>
            <code className="language-json">
              {JSON.stringify(previewData.data, null, 2)}
            </code>
          </pre>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="chat-interface-container">
      {/* HEADER - Shared component */}
      <ChatHeader />

      {/* Success/Error Notification */}
      {notification && (
        <div
          className="fixed top-4 right-4 z-50 max-w-md animate-in slide-in-from-top-5"
          style={{
            animation: "slideInFromTop 0.3s ease-out",
          }}
        >
          <div
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
              notification.type === "success"
                ? "bg-green-50 border border-green-200"
                : "bg-red-50 border border-red-200"
            }`}
          >
            {notification.type === "success" ? (
              <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            )}
            <p
              className={`text-sm font-medium ${
                notification.type === "success"
                  ? "text-green-800"
                  : "text-red-800"
              }`}
            >
              {notification.message}
            </p>
            <button
              onClick={() => setNotification(null)}
              className={`ml-auto flex-shrink-0 ${
                notification.type === "success"
                  ? "text-green-600 hover:text-green-800"
                  : "text-red-600 hover:text-red-800"
              }`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* CONTENT - Scrollable document preview */}
      <div className="chat-content-wrapper">
        <div className="document-preview-main">
          {/* Document controls bar */}
          <div className="document-preview-controls">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
              <div className="flex items-center justify-between">
                {/* Left: Back button & breadcrumb */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleBack}
                    className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    <span>Quay lại</span>
                  </button>

                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                    <span>Admin</span>
                    <span>/</span>
                    <span>{collection}</span>
                    <span>/</span>
                    <span className="font-medium text-gray-900">{docId}</span>
                  </div>
                </div>

                {/* Right: Document info & actions */}
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2 text-sm text-gray-600">
                    <FileText className="w-4 h-4" />
                    <span>
                      {type === "docx" ? "Tài liệu Word" : "Dữ liệu JSON"}
                    </span>
                    {previewData?.filename && (
                      <span className="text-gray-400">
                        • {previewData.filename}
                      </span>
                    )}
                  </div>

                  {/* Edit JSON button (only for JSON type) */}
                  {type === "json" && (
                    <button
                      onClick={handleEditJson}
                      disabled={!previewData}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                      <span>Chỉnh sửa</span>
                    </button>
                  )}

                  <button
                    onClick={handleDownload}
                    disabled={!previewData}
                    className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    <span>Tải xuống</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Document content - scrollable */}
          <div className="document-preview-content">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {renderContent()}
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER - Shared component */}
      <ChatFooter />

      {/* JSON Editor Modal */}
      {type === "json" && collection && docId && previewData?.data && (
        <JsonEditorModal
          isOpen={isEditorOpen}
          onClose={() => setIsEditorOpen(false)}
          collection={collection}
          docId={docId}
          initialData={previewData.data as Record<string, unknown>}
          onSave={handleSaveJson}
        />
      )}

      {/* Rebuild Progress Modal */}
      {collection && docId && (
        <JsonRebuildProgressModal
          isOpen={showRebuildProgress}
          onClose={() => setShowRebuildProgress(false)}
          collection={collection}
          docId={docId}
        />
      )}
    </div>
  );
};

export default DocumentPreviewPage;
