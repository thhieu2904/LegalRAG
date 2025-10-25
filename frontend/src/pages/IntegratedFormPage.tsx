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
import { ConflictDialog } from "../components/forms/ConflictDialog";
import { useFormDataManager } from "../hooks/useFormDataManager";
import { useFormDownload } from "../hooks/useFormDownload";
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
  const [isFormLoaded, setIsFormLoaded] = useState<boolean>(false);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // 🎯 PHASE 3: Sử dụng Form Data Manager hook
  const {
    cccdData,
    manualData,
    userEditedFields,
    handleManualDataChange,
    handleQRScanResult: handleQRData,
    resetQRScan: resetQRData,
    getFinalData,
    getFieldValue,
  } = useFormDataManager();

  // 🎯 PHASE A: Use form download hook for save + download flow
  const { downloadForm: saveAndDownloadForm } = useFormDownload();

  // States for conflict dialog
  const [showConflictDialog, setShowConflictDialog] = useState(false);
  const [currentConflicts, setCurrentConflicts] = useState<string[]>([]);
  const [conflictResolver, setConflictResolver] = useState<
    ((useQRData: boolean) => void) | null
  >(null);

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

  // Conflict resolution handler
  const handleConflictResolution = async (
    conflicts: string[]
  ): Promise<boolean> => {
    return new Promise((resolve) => {
      setCurrentConflicts(conflicts);
      setShowConflictDialog(true);
      setConflictResolver(() => resolve);
    });
  };

  // Xử lý kết quả QR scan với conflict detection
  const handleQRScanResult = async (data: CCCDData) => {
    await handleQRData(data, handleConflictResolution);
  };

  // Xử lý lỗi QR scan
  const handleQRScanError = (error: string) => {
    console.error("❌ QR scan lỗi:", error);
  };

  // Reset QR scan
  const resetQRScan = () => {
    resetQRData();
  };

  // Handle conflict dialog decisions
  const handleConflictDecision = (useQRData: boolean) => {
    setShowConflictDialog(false);
    if (conflictResolver) {
      conflictResolver(useQRData);
      setConflictResolver(null);
    }
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

    // 🎯 PHASE 3: Sử dụng getFinalData từ hook
    const finalData = getFinalData();

    setIsDownloading(true);
    try {
      console.log("🔄 Bắt đầu tải file Word...");
      console.log("📋 Final data to send:", finalData);

      // ✅ NEW: Check if user has CCCD data (from QR scan OR manual input)
      const hasCCCD = finalData.scan_cccd && finalData.scan_cccd.trim() !== "";

      if (hasCCCD) {
        console.log("📥 User has CCCD - using save + download flow");
        console.log("   CCCD:", finalData.scan_cccd);
        console.log("   Name:", finalData.scan_ho_ten);

        // NEW: Call fill-and-download with form data
        await saveAndDownloadForm(
          collectionId,
          docId,
          formFilename,
          finalData, // Pass all form data for filling
          finalData.scan_cccd,
          finalData.scan_ho_ten || "Unknown"
        );

        console.log("✅ File saved and downloaded");
        return;
      }

      // ❌ Fallback: No CCCD, use old flow (download only)
      console.log("⚠️ No CCCD data - using download-only flow");

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

                {/* Action buttons - Luôn hiển thị nút tải sau khi form đã load */}
                <div className="action-buttons">
                  {cccdData && (
                    <div className="auto-fill-status">🎯 Đã quét CCCD</div>
                  )}

                  {Object.keys(manualData).length > 0 && (
                    <div className="manual-fill-status">
                      ✏️ Có {Object.keys(manualData).length} thông tin thủ công
                    </div>
                  )}

                  {userEditedFields.size > 0 && (
                    <div className="edit-status">
                      📝 Đã chỉnh sửa {userEditedFields.size} trường
                    </div>
                  )}

                  {/* Luôn hiển thị nút tải sau khi form đã load */}
                  {isFormLoaded && (
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
                          {cccdData || Object.keys(manualData).length > 0
                            ? "Tải về file Word"
                            : "Tải biểu mẫu trống"}
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
                    getFieldValue={getFieldValue}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <ChatFooter />

      {/* CONFLICT DIALOG */}
      {showConflictDialog && cccdData && (
        <ConflictDialog
          isOpen={showConflictDialog}
          conflicts={currentConflicts.map((fieldName) => ({
            fieldName,
            displayName: fieldName
              .replace(/^(scan_|form_)/, "")
              .replace(/_/g, " "),
            manualValue: manualData[fieldName] || "",
            cccdValue: cccdData[fieldName as keyof CCCDData] || "",
          }))}
          onResolve={(shouldOverride) => handleConflictDecision(shouldOverride)}
          onClose={() => handleConflictDecision(false)}
        />
      )}
    </div>
  );
};

export default IntegratedFormPage;
