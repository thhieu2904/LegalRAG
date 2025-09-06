/**
 * FormRenderer Component - Giai đoạn 1 Implementation
 * Render DOCX form sử dụng dangerouslySetInnerHTML
 */

import React, { useState, useEffect } from "react";
import { identifillAPI } from "../../api/axios-config";
import "./FormRenderer.css";

interface FormRendererProps {
  collectionId: string;
  docId: string;
  formFilename: string;
  onLoadComplete?: (success: boolean) => void;
}

interface FormRenderResult {
  html_content: string;
  raw_html: string;
  form_metadata: {
    collection_id: string;
    doc_id: string;
    form_filename: string;
    conversion_success: boolean;
  };
  conversion_messages: string[];
  placeholders: string[];
}

export const FormRenderer: React.FC<FormRendererProps> = ({
  collectionId,
  docId,
  formFilename,
  onLoadComplete,
}) => {
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [formMetadata, setFormMetadata] = useState<any>(null);

  useEffect(() => {
    loadFormHTML();
  }, [collectionId, docId, formFilename]);

  const loadFormHTML = async () => {
    try {
      setLoading(true);
      setError("");

      console.log(`Loading form: ${collectionId}/${docId}/${formFilename}`);

      const response = await identifillAPI.get<{
        success: boolean;
        message: string;
        data: FormRenderResult;
      }>(`/api/v1/forms/render/${collectionId}/${docId}/${formFilename}`);

      if (response.data.success) {
        setHtmlContent(response.data.data.html_content);
        setFormMetadata(response.data.data.form_metadata);
        onLoadComplete?.(true);

        console.log("✅ Form loaded successfully");
        console.log("📋 Placeholders found:", response.data.data.placeholders);
      } else {
        throw new Error(response.data.message);
      }
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Failed to load form";
      setError(errorMessage);
      onLoadComplete?.(false);
      console.error("❌ Form loading failed:", errorMessage);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="form-renderer loading">
        <div className="loading-spinner"></div>
        <p>Đang chuyển đổi biểu mẫu từ DOCX...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="form-renderer error">
        <div className="error-content">
          <h3>⚠️ Lỗi tải biểu mẫu</h3>
          <p>{error}</p>
          <button onClick={loadFormHTML} className="retry-button">
            🔄 Thử lại
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="form-renderer">
      {/* Form metadata info */}
      {formMetadata && (
        <div className="form-header">
          <h3 className="form-title">📋 {formMetadata.form_filename}</h3>
          <p className="form-path">
            {formMetadata.collection_id} / {formMetadata.doc_id}
          </p>
        </div>
      )}

      {/* Rendered HTML content */}
      <div
        className="form-content"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />

      {/* Debug info (development only) */}
      {import.meta.env.DEV && formMetadata && (
        <div className="form-debug">
          <details>
            <summary>🔧 Debug Info</summary>
            <pre>{JSON.stringify(formMetadata, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};
