/**
 * 🔗 INTEGRATED FORM PAGE - Tích hợp QR Scan + Form Display
 * Giao diện thống nhất: QR scan bên trái + Form render bên phải
 * Cấu trúc: Header + Content (2 cột) + Footer
 */
import React, { useState } from "react";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatFooter } from "../components/chat/ChatFooter";
import { FormRenderer } from "../components/forms/FormRenderer";
import { IntegratedQRScanner } from "../components/integrated/IntegratedQRScanner";
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
  formFilename: "Khai sinh.docx",
  displayName: "Tờ khai đăng ký khai sinh",
};

const IntegratedFormPage = () => {
  const [selectedForm] = useState<FormSelection>(DEFAULT_FORM); // Fixed form
  const [cccdData, setCccdData] = useState<CCCDData | null>(null);
  const [isFormLoaded, setIsFormLoaded] = useState<boolean>(false);

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

              {/* Form Status */}
              <div className="form-status-bar">
                <div
                  className={`form-status-indicator ${
                    isFormLoaded ? "loaded" : "loading"
                  }`}
                >
                  {isFormLoaded ? "✅ Form đã tải" : "⏳ Đang tải form..."}
                </div>
                {cccdData ? (
                  <div className="auto-fill-status">
                    🎯 Sẵn sàng điền tự động
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
