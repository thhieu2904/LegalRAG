/**
 * 🔗 INTEGRATED FORM PAGE - Tích hợp QR Scan + Form Display + Download
 * Giao diện thống nhất: QR scan bên trái + Form render bên phải + Download button
 * Cấu trúc: Header + Content (2 cột) + Footer
 */
import React, { useState } from "react";
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

      // Call identifill_service API
      const response = await fetch(
        `http://localhost:8002/api/v1/forms/fill-and-download/${selectedForm.collectionId}/${selectedForm.docId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            scan_ho_ten: cccdData.full_name,
            scan_ngay_sinh: cccdData.date_of_birth,
            scan_dia_chi: cccdData.address,
            scan_cccd: cccdData.citizen_id,
            scan_gioi_tinh: cccdData.gender,
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
                      🎯 Sẵn sàng điền tự động
                    </div>
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
                  <div className="manual-fill-status">✏️ Điền thủ công</div>
                )}
              </div>

              {/* Form Renderer */}
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
