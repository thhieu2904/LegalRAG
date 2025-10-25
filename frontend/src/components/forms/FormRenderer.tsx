/**
 * FormRenderer Component - Giai đoạn 2 Implementation cho DOCX form
 * Sử dụng formAPI mới và hiển thị HTML form với placeholder hydration
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import type { Root } from "react-dom/client";
import type { AxiosError } from "axios";
import { formAPI } from "../../api/form-api";
import { EditablePlaceholder } from "./EditablePlaceholder";
import { useFormDownload } from "../../hooks/useFormDownload";
import "./FormRenderer.css";

interface FormRendererProps {
  collectionId: string;
  docId: string;
  formFilename: string;
  onLoadComplete?: (success: boolean) => void;
  manualData?: Record<string, string>; // Manual input data từ parent
  onManualDataChange?: (fieldName: string, value: string) => void; // Callback cập nhật manual data
  cccdData?: Record<string, string>; // CCCD scan data để reference
  getFieldValue?: (fieldName: string) => string; // NEW: Function để lấy final value
  getFieldSource?: (fieldName: string) => "manual" | "cccd" | "empty"; // NEW: Function để lấy nguồn data
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
  manualData = {},
  onManualDataChange,
  cccdData = {},
  getFieldValue,
  getFieldSource,
}) => {
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [formMetadata, setFormMetadata] = useState<
    FormRenderResult["form_metadata"] | null
  >(null);

  // 🎉 NEW: Download and storage states
  const { downloadForm, loading: downloadLoading } = useFormDownload();
  const [notification, setNotification] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const reactRootsRef = useRef<Map<HTMLElement, Root>>(new Map());
  const isHydratedRef = useRef<boolean>(false);
  const formContentRef = useRef<HTMLDivElement>(null);
  const htmlSetRef = useRef<boolean>(false);

  // Cleanup React roots khi component unmount
  useEffect(() => {
    const currentRoots = reactRootsRef.current;
    return () => {
      currentRoots.forEach((root, element) => {
        try {
          // 🎯 Clean up class trước khi unmount
          element.classList.remove("react-hydrated");
          root.unmount();
        } catch (e) {
          console.warn("Error unmounting React root:", e);
        }
      });
      currentRoots.clear();
      // 🎯 Reset hydration state
      isHydratedRef.current = false;
    };
  }, []);

  // BƯỚC 1: Hydration Logic - CHỈ hydrate form placeholders
  const hydratePlaceholders = useCallback(() => {
    // 🎯 PREVENT multiple hydration calls
    if (isHydratedRef.current) {
      console.log("⏭️ Skipping hydration - already hydrated");
      return;
    }

    console.log("🔄 Starting placeholder hydration...");

    const formContainer = document.querySelector(".form-content");
    if (!formContainer) {
      console.warn("⚠️ Form container not found for hydration");
      return;
    }

    // 🎯 Hydrate cả FORM và SCAN placeholders (manual input)
    const allPlaceholderElements = formContainer.querySelectorAll(
      '[class^="placeholder_form_"], [class^="placeholder_scan_"]'
    );
    console.log(
      `📍 Found ${allPlaceholderElements.length} placeholders (FORM + SCAN) to hydrate`
    );

    let hydratedCount = 0;
    allPlaceholderElements.forEach((element) => {
      const htmlElement = element as HTMLElement;

      // Extract field name từ class (hỗ trợ cả placeholder_form_ và placeholder_scan_)
      const className = Array.from(htmlElement.classList).find(
        (cls) =>
          cls.startsWith("placeholder_form_") ||
          cls.startsWith("placeholder_scan_")
      );
      if (!className) return;

      // Chuẩn hóa field name cho cả form và scan
      let fieldName: string;
      if (className.startsWith("placeholder_form_")) {
        fieldName = className.replace("placeholder_form_", "form_");
      } else if (className.startsWith("placeholder_scan_")) {
        fieldName = className.replace("placeholder_scan_", "scan_");
      } else {
        return; // Không hỗ trợ format khác
      }

      // Skip nếu đã được hydrate
      if (reactRootsRef.current.has(htmlElement)) {
        console.log(`⏭️ Skipping already hydrated: ${fieldName}`);
        return;
      }

      try {
        // BƯỚC 2: Tạo React root và render EditablePlaceholder
        const root = createRoot(htmlElement);
        reactRootsRef.current.set(htmlElement, root);

        // 🎯 IMPORTANT: Đánh dấu element đã được React hydrate để tránh CSS conflicts
        htmlElement.classList.add("react-hydrated");

        root.render(
          <EditablePlaceholder
            fieldName={fieldName}
            value={
              getFieldValue
                ? getFieldValue(fieldName)
                : manualData[fieldName] || ""
            }
            cccdValue={cccdData[fieldName]}
            onSave={(field, value) => {
              onManualDataChange?.(field, value);
            }}
            placeholder={`Nhập ${fieldName.replace(/_/g, " ")}`}
          />
        );

        hydratedCount++;
        console.log(`✅ Hydrated FORM placeholder: ${fieldName}`);
      } catch (error) {
        console.error(`❌ Error hydrating ${fieldName}:`, error);
      }
    });

    // 🎯 Mark as hydrated only if we actually hydrated elements
    if (hydratedCount > 0) {
      isHydratedRef.current = true;
      console.log(
        `✅ Placeholder hydration completed - ${hydratedCount} elements hydrated`
      );
    }
  }, [manualData, cccdData, onManualDataChange, getFieldValue]);

  // BƯỚC 3: Update React components khi manual data thay đổi (WITHOUT re-hydration)
  // 🎯 FIX: Re-render React components khi data thay đổi
  const updateReactComponents = useCallback(() => {
    if (!isHydratedRef.current) return;

    console.log("🔄 Re-rendering React components with new data");

    reactRootsRef.current.forEach((root, element) => {
      const className = Array.from(element.classList).find(
        (cls) =>
          cls.startsWith("placeholder_form_") ||
          cls.startsWith("placeholder_scan_")
      );
      if (!className) return;

      // Chuẩn hóa field name
      let fieldName: string;
      if (className.startsWith("placeholder_form_")) {
        fieldName = className.replace("placeholder_form_", "form_");
      } else if (className.startsWith("placeholder_scan_")) {
        fieldName = className.replace("placeholder_scan_", "scan_");
      } else {
        return;
      }

      // Re-render với data mới
      root.render(
        <EditablePlaceholder
          fieldName={fieldName}
          value={
            getFieldValue
              ? getFieldValue(fieldName)
              : manualData[fieldName] || ""
          }
          cccdValue={cccdData[fieldName]}
          onSave={(field, value) => {
            onManualDataChange?.(field, value);
          }}
          placeholder={`Nhập ${fieldName.replace(/_/g, " ")}`}
        />
      );
    });
  }, [manualData, cccdData, getFieldValue, onManualDataChange]); // BƯỚC 3: Set HTML content chỉ 1 lần và hydrate
  useEffect(() => {
    if (
      htmlContent &&
      !loading &&
      formContentRef.current &&
      !htmlSetRef.current
    ) {
      console.log("🎯 Setting HTML content for the FIRST and ONLY time");

      // Set HTML content manually để tránh dangerouslySetInnerHTML re-render
      formContentRef.current.innerHTML = htmlContent;
      htmlSetRef.current = true;

      // Trigger hydration after HTML is set
      setTimeout(() => {
        hydratePlaceholders();
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [htmlContent, loading]); // 🎯 Remove hydratePlaceholders dependency to prevent re-runs

  // 🎯 FIX: Re-render React components khi data thay đổi
  useEffect(() => {
    if (isHydratedRef.current) {
      console.log("🔄 Data changed, re-rendering React components:", {
        manualDataKeys: Object.keys(manualData),
        cccdDataKeys: Object.keys(cccdData),
      });
      updateReactComponents();
    }
  }, [manualData, cccdData, updateReactComponents]);

  const loadFormHTML = useCallback(async () => {
    console.log(`🔔 loadFormHTML CALLED - Render ID: ${Date.now()}`);
    try {
      setLoading(true);
      setError("");

      // 🎯 Reset hydration state when loading new form
      if (isHydratedRef.current) {
        console.log("🔄 Resetting hydration state for new form load");
        isHydratedRef.current = false;
        htmlSetRef.current = false; // 🎯 Allow HTML to be set again

        // Clear existing content
        if (formContentRef.current) {
          formContentRef.current.innerHTML = "";
        }
      }

      console.log(
        `📡 API Call: Loading form ${collectionId}/${docId}/${formFilename}`
      );

      const result = await formAPI.renderForm(
        collectionId,
        docId,
        formFilename
      );

      setHtmlContent(result.html_content);
      setFormMetadata({
        collection_id: result.form_metadata.collection_id,
        doc_id: result.form_metadata.doc_id,
        form_filename: result.form_metadata.form_filename,
        conversion_success: true, // Default to true since API succeeded
      });
      onLoadComplete?.(true);

      console.log("✅ Form loaded successfully");
      console.log("📋 Placeholders found:", result.placeholders);
    } catch (err: unknown) {
      const error = err as Error;
      const errorMessage = error.message || "Failed to load form";
      setError(errorMessage);
      onLoadComplete?.(false);
      console.error("❌ Form loading failed:", errorMessage);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collectionId, docId, formFilename]); // 🎯 Remove onLoadComplete to prevent recreation

  useEffect(() => {
    console.log(`🔔 useEffect TRIGGER: Loading form due to dependency change`, {
      collectionId,
      docId,
      formFilename,
    });
    loadFormHTML();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collectionId, docId, formFilename]); // 🎯 Use direct dependencies to prevent multiple calls

  // Handle download and auto-save
  const handleDownloadForm = useCallback(async () => {
    try {
      setNotification({
        type: "info",
        message: "🔄 Đang lưu và tải biểu mẫu...",
      });

      const formPath = `${collectionId}/${docId}/${formFilename}`;
      const cccdValue = cccdData.scan_cccd || "";
      const userName = cccdData.scan_ho_ten || "";
      const formName = formFilename.replace(".docx", "");

      await downloadForm(formPath, cccdValue, userName, formName, formFilename);

      setNotification({
        type: "success",
        message: "✅ Biểu mẫu đã được tải xuống và lưu thành công!",
      });

      // Clear notification after 3 seconds
      setTimeout(() => {
        setNotification(null);
      }, 3000);
    } catch (error: unknown) {
      let errorMsg = "Không thể tải biểu mẫu";

      if (error instanceof Error) {
        errorMsg = error.message;
      }

      const axiosError = error as AxiosError<Record<string, unknown>>;
      if (
        axiosError?.response?.data &&
        typeof axiosError.response.data === "object" &&
        "detail" in axiosError.response.data
      ) {
        errorMsg = String(axiosError.response.data.detail);
      }

      setNotification({
        type: "error",
        message: `❌ Lỗi tải: ${errorMsg}`,
      });
    }
  }, [
    collectionId,
    docId,
    formFilename,
    cccdData.scan_cccd,
    cccdData.scan_ho_ten,
    downloadForm,
  ]);

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
      {/* Notification Display */}
      {notification && (
        <div
          className={`form-notification form-notification-${notification.type}`}
        >
          <p>{notification.message}</p>
        </div>
      )}

      {/* Form metadata info with download button */}
      {formMetadata && (
        <div className="form-header">
          <div className="form-header-left">
            <h3 className="form-title">📋 {formMetadata.form_filename}</h3>
            <p className="form-path">
              {formMetadata.collection_id} / {formMetadata.doc_id}
            </p>
          </div>
          <div className="form-header-actions">
            <button
              onClick={handleDownloadForm}
              disabled={downloadLoading}
              className="download-button"
              title="Tải xuống và lưu biểu mẫu"
            >
              {downloadLoading ? "⏳ Đang tải..." : "⬇️ Tải xuống"}
            </button>
          </div>
        </div>
      )}

      {/* Rendered HTML content - Set via ref to prevent re-render destruction */}
      <div
        ref={formContentRef}
        className="form-content"
        // NO dangerouslySetInnerHTML - content set via useEffect + ref
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
