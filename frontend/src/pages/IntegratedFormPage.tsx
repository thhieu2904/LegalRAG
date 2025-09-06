/**
 * 🔗 INTEGRATED FORM PAGE - Tích hợp QR Scan + Form Display + Download
 * Giao diện thống nhất: QR scan bên trái + Form render bên phải + Download button
 * Cấu trúc: Header + Content (2 cột) + Footer
 */
import { useState, useEffect } from "react";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatFooter } from "../components/chat/ChatFooter";
import { FormRenderer } from "../components/forms/FormRenderer";
import { IntegratedQRScanner } from "../components/integrated/IntegratedQRScanner";
import { Download, Loader } from "lucide-react";
import type { CCCDData } from "../api/qr-scanner-api";
import "./IntegratedFormPageNew.css";

interface FormSelection {
  collectionId: string;
  docId: string;
  formFilename: string;
  displayName: string;
}

// Fixed form - không cần chọn nhiều forms
const DEFAULT_FORM: FormSelection = {
  collectionId: "quy_trinh_cap_ho_tich_cap_xa",
  docId: "DOC_001",
  formFilename: "Khai_sinh.docx",
  displayName: "Tờ khai đăng ký khai sinh",
};

const IntegratedFormPage = () => {
  const [selectedForm] = useState<FormSelection>(DEFAULT_FORM); // Fixed form
  const [cccdData, setCccdData] = useState<CCCDData | null>(null);
  const [isFormLoaded, setIsFormLoaded] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // 🎨 Auto Form Preview - Generic placeholder filling (no hardcode mapping!)
  const highlightFormFields = (cccdData: CCCDData) => {
    console.log("🎨 Generic filling placeholders with CCCD data:", cccdData);

    const formContainer = document.querySelector(".form-renderer-container");
    if (!formContainer) {
      console.warn("⚠️ Form container not found for placeholder replacement");
      return;
    }

    // Tìm tất cả placeholder elements [class^="placeholder_"]
    const placeholderElements = formContainer.querySelectorAll(
      '[class^="placeholder_"]'
    );

    placeholderElements.forEach((element) => {
      // Extract placeholder name từ class
      const className = Array.from(element.classList).find((cls) =>
        cls.startsWith("placeholder_")
      );
      if (!className) return;

      const fieldName = className.replace("placeholder_", ""); // scan_ho_ten, scan_cccd, etc.

      // 🎯 GENERIC: Direct mapping từ placeholder name tới CCCD field
      const cccdValue = (cccdData as unknown as Record<string, string>)[
        fieldName
      ];

      if (cccdValue) {
        // Lưu original text nếu chưa có
        if (!element.getAttribute("data-original-text")) {
          element.setAttribute("data-original-text", element.textContent || "");
        }

        // 🎯 UX: Thay thế {{placeholder}} với CCCD data hoặc ẩn nếu empty
        const originalText = element.textContent || "";
        if (originalText.includes("{{") && originalText.includes("}}")) {
          // Thay thế placeholder với data
          const newText = originalText.replace(/\{\{[^}]+\}\}/g, cccdValue);
          element.textContent = newText;
        }

        // 🎯 CSS STATE: Mark element as filled để trigger CSS styling
        element.setAttribute("data-filled", "true");
        element.classList.add("filled");
        element.setAttribute("data-cccd-value", cccdValue);
        element.setAttribute("title", `CCCD: ${cccdValue}`);

        console.log(`🔄 Filled "${className}": ${fieldName} → "${cccdValue}"`);
      }
    });

    console.log("✅ Auto form preview completed with class-based approach");
  };

  // Auto-highlight when CCCD is scanned
  useEffect(() => {
    if (cccdData && isFormLoaded) {
      // Small delay to ensure form is fully rendered
      setTimeout(() => {
        highlightFormFields(cccdData);
      }, 500);
    }
  }, [cccdData, isFormLoaded]);

  // Xử lý kết quả QR scan
  const handleQRScanResult = (data: CCCDData) => {
    setCccdData(data);
    console.log("✅ QR scan thành công:", data);
  };

  // Xử lý lỗi QR scan
  const handleQRScanError = (error: string) => {
    console.error("❌ QR scan lỗi:", error);
  };

  // Reset QR scan
  const resetQRScan = () => {
    setCccdData(null);
  };

  // Xử lý form load complete
  const handleFormLoadComplete = (success: boolean) => {
    setIsFormLoaded(success);
  };

  // Download filled form - NHIỆM VỤ 3
  const handleDownloadFilledForm = async () => {
    if (!cccdData) {
      alert("Vui lòng quét CCCD trước khi tải về");
      return;
    }

    setIsDownloading(true);
    try {
      console.log("🔄 Bắt đầu tải file Word...");

      // Dùng cùng file cho cả hiển thị và fill/download
      const templateName = selectedForm.formFilename;
      console.log(`📋 Using same file for display and fill: ${templateName}`);

      // Call identifill_service API
      const response = await fetch(
        `http://localhost:8002/api/v1/forms/fill-and-download/${selectedForm.collectionId}/${selectedForm.docId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            scan_ho_ten: cccdData.scan_ho_ten,
            scan_ngay_sinh: cccdData.scan_ngay_sinh,
            scan_dia_chi: cccdData.scan_dia_chi,
            scan_cccd: cccdData.scan_cccd,
            scan_gioi_tinh: cccdData.scan_gioi_tinh,
            template_name: templateName, // Dynamic template mapping
          }),
        }
      );

      if (response.ok) {
        // Get the blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${selectedForm.displayName}_filled.docx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        console.log("✅ File đã được tải xuống thành công");
      } else {
        const errorText = await response.text();
        console.error("❌ Lỗi tải file:", errorText);
        alert(`Lỗi tải file: ${errorText}`);
      }
    } catch (error) {
      console.error("❌ Lỗi kết nối:", error);
      alert("Lỗi kết nối đến server. Vui lòng thử lại.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="integrated-form-container">
      {/* HEADER */}
      <ChatHeader />

      {/* CONTENT - 2 cột */}
      <div className="integrated-form-content">
        <div className="integrated-form-layout">
          {/* BÊN TRÁI: QR Scanner */}
          <div className="qr-scanner-section">
            <IntegratedQRScanner
              onResult={handleQRScanResult}
              onError={handleQRScanError}
              cccdData={cccdData}
              onReset={resetQRScan}
            />
          </div>

          {/* BÊN PHẢI: Form Display */}
          <div className="form-display-section">
            <div className="form-display-card">
              {/* Form Header */}
              <div className="form-display-header">
                <h2 className="form-display-title">
                  📄 {selectedForm.displayName}
                </h2>
                <p className="form-display-subtitle">
                  {selectedForm.collectionId} / {selectedForm.docId}
                </p>
              </div>

              {/* Form Status & Download */}
              <div className="form-status-bar">
                <div
                  className={`form-status-indicator ${
                    isFormLoaded ? "loaded" : "loading"
                  }`}
                >
                  {isFormLoaded ? "✅ Form đã tải" : "⏳ Đang tải form..."}
                </div>

                {cccdData ? (
                  <div className="action-buttons">
                    <div className="auto-fill-status">
                      🎯 Auto preview đang hiển thị
                    </div>

                    {/* Download Button */}
                    <button
                      onClick={handleDownloadFilledForm}
                      disabled={isDownloading}
                      className="download-button"
                    >
                      {isDownloading ? (
                        <>
                          <Loader className="spinner" size={16} />
                          Đang tải...
                        </>
                      ) : (
                        <>
                          <Download size={16} />
                          Tải về file Word
                        </>
                      )}
                    </button>
                  </div>
                ) : (
                  <div className="manual-fill-status">
                    ✏️ Quét CCCD để auto-fill
                  </div>
                )}
              </div>

              {/* Form Renderer - Simple display */}
              <div className="form-renderer-container">
                <FormRenderer
                  collectionId={selectedForm.collectionId}
                  docId={selectedForm.docId}
                  formFilename={selectedForm.formFilename}
                  onLoadComplete={handleFormLoadComplete}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <ChatFooter />
    </div>
  );
};

export default IntegratedFormPage;
