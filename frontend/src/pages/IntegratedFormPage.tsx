/**
 * 🔗 INTEGRATED FORM PAGE - Tích hợp QR Scan + Form Display + Download
 * Giao diện thống nhất: QR scan bên trái + Form render bên phải + Download button
 * Cấu trúc: Header + Content (2 cột) + Footer
 * DYNAMIC FORM LOADING: Nhận tham số từ URL thay vì dùng DEFAULT_FORM
 */
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatFooter } from "../components/chat/ChatFooter";
import { FormRenderer } from "../components/forms/FormRenderer";
import { IntegratedQRScanner } from "../components/integrated/IntegratedQRScanner";
import { Download, Loader, AlertCircle } from "lucide-react";
import { formAPI } from "../api/form-api";
import type { CCCDData } from "../api/qr-scanner-api";
import type { FormRenderResult } from "../api/form-api";
import "./IntegratedFormPageNew.css";

const IntegratedFormPage = () => {
  // 🎯 DYNAMIC ROUTING: Lấy tham số từ URL
  const { collectionId, docId, formFilename } = useParams<{
    collectionId: string;
    docId: string;
    formFilename: string;
  }>();

  // States
  const [formData, setFormData] = useState<FormRenderResult | null>(null);
  const [formLoading, setFormLoading] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [cccdData, setCccdData] = useState<CCCDData | null>(null);
  const [isFormLoaded, setIsFormLoaded] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // 🎯 PHASE 3: State trung tâm cho manual data
  const [manualData, setManualData] = useState<Record<string, string>>({});

  // Load form khi component mount hoặc tham số thay đổi
  useEffect(() => {
    const loadForm = async () => {
      if (collectionId && docId && formFilename) {
        await loadFormData();
      }
    };
    loadForm();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [collectionId, docId, formFilename]);

  // Load form data từ API
  const loadFormData = async () => {
    if (!collectionId || !docId || !formFilename) {
      setFormError("Thiếu tham số form trong URL");
      return;
    }

    setFormLoading(true);
    setFormError(null);

    try {
      console.log(`🔍 Loading form: ${collectionId}/${docId}/${formFilename}`);

      const result = await formAPI.loadFormComplete(
        collectionId,
        docId,
        formFilename
      );

      setFormData(result.rendered);
      setIsFormLoaded(true);
      console.log("✅ Form loaded successfully");
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Lỗi không xác định";
      setFormError(errorMessage);
      console.error("❌ Error loading form:", error);
    } finally {
      setFormLoading(false);
    }
  };

  // 🎯 PHASE 3: Callback để cập nhật manual data từ EditablePlaceholder
  const handleManualDataChange = (fieldName: string, value: string) => {
    setManualData((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
    console.log(`✏️ Manual data updated: ${fieldName} = "${value}"`);
  };

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
    // 🎯 PHASE 3: Reset manual data khi reset QR scan (optional)
    // setManualData({}); // Uncomment if you want to clear manual data on QR reset
  };

  // Xử lý form load complete
  const handleFormLoadComplete = (success: boolean) => {
    setIsFormLoaded(success);
  };

  // Download filled form - NHIỆM VỤ 3
  const handleDownloadFilledForm = async () => {
    if (!collectionId || !docId || !formFilename) {
      alert("Thông tin form không đầy đủ");
      return;
    }

    // 🎯 PHASE 3: Merge CCCD data với manual data
    const finalData = {
      ...cccdData, // CCCD data làm base
      ...manualData, // Manual data có priority cao hơn (override CCCD nếu có)
    };

    if (!cccdData && Object.keys(manualData).length === 0) {
      alert("Vui lòng quét CCCD hoặc nhập thông tin thủ công trước khi tải về");
      return;
    }

    setIsDownloading(true);
    try {
      console.log("🔄 Bắt đầu tải file Word...");
      console.log("📋 Final data to send:", finalData);

      // Dùng cùng file cho cả hiển thị và fill/download
      console.log(`📋 Using same file for display and fill: ${formFilename}`);

      // Call identifill_service API với merged data
      const response = await fetch(
        `http://localhost:8002/api/v1/forms/fill-and-download/${collectionId}/${docId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...finalData, // Spread merged data
            template_name: formFilename, // Dynamic template mapping
          }),
        }
      );

      if (response.ok) {
        // Get the blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${formFilename}_filled.docx`;
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
                  📄 {formFilename || "Biểu mẫu"}
                </h2>
                <p className="form-display-subtitle">
                  {collectionId} / {docId}
                </p>
              </div>

              {/* Loading State */}
              {formLoading && (
                <div className="form-loading-state">
                  <Loader className="spinning" size={24} />
                  <span>Đang tải biểu mẫu...</span>
                </div>
              )}

              {/* Error State */}
              {formError && (
                <div className="form-error-state">
                  <AlertCircle size={24} />
                  <span>{formError}</span>
                </div>
              )}

              {/* Form Status & Download */}
              <div className="form-status-bar">
                <div
                  className={`form-status-indicator ${
                    isFormLoaded ? "loaded" : "loading"
                  }`}
                >
                  {isFormLoaded ? "✅ Form đã tải" : "⏳ Đang tải form..."}
                </div>

                {/* Action buttons - Updated với manual data logic */}
                <div className="action-buttons">
                  {cccdData && (
                    <div className="auto-fill-status">
                      🎯 Auto preview đang hiển thị
                    </div>
                  )}

                  {Object.keys(manualData).length > 0 && (
                    <div className="manual-fill-status">
                      ✏️ Có {Object.keys(manualData).length} thông tin thủ công
                    </div>
                  )}

                  {(cccdData || Object.keys(manualData).length > 0) && (
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
                  )}

                  {!cccdData && Object.keys(manualData).length === 0 && (
                    <div className="manual-fill-status">
                      ✏️ Quét CCCD hoặc click để nhập thông tin
                    </div>
                  )}
                </div>
              </div>

              {/* Form Renderer - Simple display */}
              <div className="form-renderer-container">
                {formData && !formLoading && !formError && (
                  <FormRenderer
                    collectionId={collectionId!}
                    docId={docId!}
                    formFilename={formFilename!}
                    onLoadComplete={handleFormLoadComplete}
                    manualData={manualData}
                    onManualDataChange={handleManualDataChange}
                    cccdData={
                      cccdData
                        ? (cccdData as unknown as Record<string, string>)
                        : {}
                    }
                  />
                )}
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
