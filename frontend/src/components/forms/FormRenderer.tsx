/**
 * FormRenderer Component - Giai đoạn 2 Implement  // Cleanup React roots khi component unmount
  useEffect(() => {
    const currentRoots = reactRootsRef.current;
    return () => {
      currentRoots.forEach((root, element) => {
        try {
          // Remove React hydrated class
          element.classList.remove('react-hydrated');
          root.unmount();
        } catch (e) {
          console.warn('Error unmounting React root:', e);
        }
      });
      currentRoots.clear();
    };
  }, []);r DOCX form sử dụng dangerouslySetInnerHTML + React Hydration
 * Tạo "Giả Inline Edit" với Popover sử dụng useEffect & createRoot
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import type { Root } from "react-dom/client";
import { identifillAPI } from "../../api/axios-config";
import { EditablePlaceholder } from "./EditablePlaceholder";
import "./FormRenderer.css";

interface FormRendererProps {
  collectionId: string;
  docId: string;
  formFilename: string;
  onLoadComplete?: (success: boolean) => void;
  manualData?: Record<string, string>; // Manual input data từ parent
  onManualDataChange?: (fieldName: string, value: string) => void; // Callback cập nhật manual data
  cccdData?: Record<string, string>; // CCCD scan data để reference
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
}) => {
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [formMetadata, setFormMetadata] = useState<
    FormRenderResult["form_metadata"] | null
  >(null);
  const reactRootsRef = useRef<Map<HTMLElement, Root>>(new Map());
  const isHydratedRef = useRef<boolean>(false); // 🎯 Track hydration status
  const formContentRef = useRef<HTMLDivElement>(null); // 🎯 Ref to form content div
  const htmlSetRef = useRef<boolean>(false); // 🎯 Track if HTML has been set

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

    // 🎯 CHỈ hydrate FORM placeholders (manual input)
    const formPlaceholderElements = formContainer.querySelectorAll(
      '[class^="placeholder_form_"]'
    );
    console.log(
      `📍 Found ${formPlaceholderElements.length} FORM placeholders to hydrate`
    );

    let hydratedCount = 0;
    formPlaceholderElements.forEach((element) => {
      const htmlElement = element as HTMLElement;

      // Extract field name từ class (placeholder_form_xxx → form_xxx)
      const className = Array.from(htmlElement.classList).find((cls) =>
        cls.startsWith("placeholder_form_")
      );
      if (!className) return;

      const fieldName = className.replace("placeholder_form_", "form_"); // Chuẩn hóa field name

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
            value={manualData[fieldName] || ""}
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
  }, [manualData, cccdData, onManualDataChange]);

  // BƯỚC 3: Update React components khi manual data thay đổi (WITHOUT re-hydration)
  const updatePlaceholderValues = useCallback(() => {
    if (!formContentRef.current) return;

    // BƯỚC 1: Update SCAN placeholders (auto-fill từ CCCD)
    const scanPlaceholderElements = formContentRef.current.querySelectorAll(
      '[class^="placeholder_scan_"]:not(.react-hydrated)'
    );

    scanPlaceholderElements.forEach((element) => {
      const className = Array.from(element.classList).find((cls) =>
        cls.startsWith("placeholder_scan_")
      );
      if (!className) return;

      const fieldName = className.replace("placeholder_scan_", "scan_");
      const htmlElement = element as HTMLElement;

      // Lấy value từ cccdData (scan data)
      const value = cccdData[fieldName] || "";

      if (value) {
        // Auto-fill SCAN data
        htmlElement.textContent = value;
        htmlElement.setAttribute("data-filled", "true");
        htmlElement.classList.add("filled");
        console.log(`✅ Auto-filled SCAN ${fieldName} = "${value}"`);
      } else {
        // Reset về placeholder state
        htmlElement.textContent = `{{${className}}}`;
        htmlElement.removeAttribute("data-filled");
        htmlElement.classList.remove("filled");
      }
    });

    // BƯỚC 2: Update FORM placeholders (non-React ones)
    const formPlaceholderElements = formContentRef.current.querySelectorAll(
      '[class^="placeholder_form_"]:not(.react-hydrated)'
    );

    formPlaceholderElements.forEach((element) => {
      const className = Array.from(element.classList).find((cls) =>
        cls.startsWith("placeholder_form_")
      );
      if (!className) return;

      const fieldName = className.replace("placeholder_form_", "form_");
      const htmlElement = element as HTMLElement;

      // Lấy value từ manualData (manual input)
      const value = manualData[fieldName] || "";

      if (value) {
        // Fill manual data
        htmlElement.textContent = value;
        htmlElement.setAttribute("data-filled", "true");
        htmlElement.classList.add("filled");
        console.log(`✅ Filled FORM ${fieldName} = "${value}"`);
      } else {
        // Reset về placeholder state
        htmlElement.textContent = `{{${className}}}`;
        htmlElement.removeAttribute("data-filled");
        htmlElement.classList.remove("filled");
      }
    });

    // BƯỚC 3: Update React components (CHỈ FORM placeholders)
    reactRootsRef.current.forEach((root, element) => {
      const className = Array.from(element.classList).find((cls) =>
        cls.startsWith("placeholder_form_")
      );
      if (!className) return;

      const fieldName = className.replace("placeholder_form_", "form_");
      const value = manualData[fieldName] || "";

      // Đánh dấu filled state cho React element (chỉ attributes, KHÔNG textContent)
      if (value) {
        element.setAttribute("data-filled", "true");
        element.classList.add("filled");
      } else {
        element.removeAttribute("data-filled");
        element.classList.remove("filled");
      }

      // Re-render React component với giá trị mới
      root.render(
        <EditablePlaceholder
          fieldName={fieldName}
          value={manualData[fieldName] || ""}
          cccdValue={cccdData[fieldName]}
          onSave={(field, value) => {
            onManualDataChange?.(field, value);
          }}
          placeholder={`Nhập ${fieldName.replace(/_/g, " ")}`}
        />
      );

      console.log(
        `✅ Updated React component ${fieldName} with CCCD: ${
          cccdData[fieldName] || "none"
        }`
      );
    });

    console.log(
      "🔄 Updated both HTML content (non-React) and React components separately"
    );
  }, [manualData, cccdData, onManualDataChange]); // BƯỚC 3: Set HTML content chỉ 1 lần và hydrate
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

  // BƯỚC 4: Update values khi manual data thay đổi (không re-hydrate)
  useEffect(() => {
    if (
      isHydratedRef.current &&
      (Object.keys(manualData).length > 0 || Object.keys(cccdData).length > 0)
    ) {
      console.log("🔄 Updating placeholder values (no re-hydration):", {
        manualDataKeys: Object.keys(manualData),
        cccdDataKeys: Object.keys(cccdData),
      });
      updatePlaceholderValues();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [manualData, cccdData]); // 🎯 Remove updatePlaceholderValues dependency

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
