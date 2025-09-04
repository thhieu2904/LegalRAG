/**
 * 🔗 INTEGRATED FORM PAGE - Tích hợp QR Scan + Form Display
 * Giao diện thống nhất: QR scan bên trái + Form render bên phải
 * Cấu trúc: Header + Content (2 cột) + Footer
 */
import React, { useState } from "react";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatFooter } from "../components/chat/ChatFooter";
import { FormRenderer } from "../components/forms/FormRenderer";
import { QRScanner } from "../components/qrscan/QRScanner";
import { Camera, Upload } from "lucide-react";
import type { CCCDData } from "../api/qr-scanner-api";
import "./IntegratedFormPage.css";

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
  const [qrScanStatus, setQrScanStatus] = useState<
    "idle" | "scanning" | "success" | "error"
  >("idle");
  const [scanMethod, setScanMethod] = useState<"camera" | "upload">("camera"); // Add scan method
  const [isFormLoaded, setIsFormLoaded] = useState<boolean>(false);

  // Xử lý kết quả QR scan
  const handleQRScanResult = (data: CCCDData) => {
    setCccdData(data);
    setQrScanStatus("success");
    console.log("✅ QR scan thành công:", data);
  };

  // Xử lý lỗi QR scan
  const handleQRScanError = (error: string) => {
    setQrScanStatus("error");
    console.error("❌ QR scan lỗi:", error);
  };

  // Xử lý upload file ảnh
  const handleImageUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setQrScanStatus("scanning");

    try {
      // Tạo FormData để upload
      const formData = new FormData();
      formData.append("file", file);

      // Gọi API QR scan (sẽ implement sau)
      const response = await fetch("http://localhost:8002/api/v1/qr/scan", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          handleQRScanResult(result.data);
        } else {
          throw new Error(result.message || "QR scan failed");
        }
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      handleQRScanError(
        error instanceof Error ? error.message : "Unknown error"
      );
    }
  };

  // Reset QR scan
  const resetQRScan = () => {
    setCccdData(null);
    setQrScanStatus("idle");
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
            <div className="qr-scanner-card">
              {/* QR Scanner Header */}
              <div className="qr-scanner-header">
                <h2 className="qr-scanner-title">📱 Truy xuất CCCD</h2>
                <p className="qr-scanner-subtitle">
                  Quét trực tiếp từ camera hoặc tải ảnh CCCD để tự động điền
                  thông tin
                </p>
              </div>

              {/* Scan Method Tabs */}
              <div className="scan-method-tabs">
                <button
                  onClick={() => setScanMethod("camera")}
                  className={`method-tab ${
                    scanMethod === "camera" ? "active" : ""
                  }`}
                >
                  <Camera size={20} />
                  <span>Camera</span>
                </button>
                <button
                  onClick={() => setScanMethod("upload")}
                  className={`method-tab ${
                    scanMethod === "upload" ? "active" : ""
                  }`}
                >
                  <Upload size={20} />
                  <span>Tải ảnh</span>
                </button>
              </div>

              {/* Scanner Content */}
              <div className="qr-scanner-content">
                {scanMethod === "camera" ? (
                  <QRScanner
                    onResult={handleQRScanResult}
                    onError={handleQRScanError}
                    className="integrated-qr-scanner"
                  />
                ) : (
                  <div className="qr-upload-area">
                    <div className={`qr-upload-zone ${qrScanStatus}`}>
                      {qrScanStatus === "idle" && (
                        <>
                          <div className="qr-upload-icon">📷</div>
                          <p className="qr-upload-text">
                            Chọn ảnh CCCD để quét
                          </p>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleImageUpload}
                            className="qr-upload-input"
                            id="qr-upload"
                          />
                          <label
                            htmlFor="qr-upload"
                            className="qr-upload-button"
                          >
                            Chọn ảnh
                          </label>
                        </>
                      )}

                      {qrScanStatus === "scanning" && (
                        <div className="qr-scanning-state">
                          <div className="qr-scanning-spinner"></div>
                          <p className="qr-scanning-text">Đang quét...</p>
                        </div>
                      )}

                      {qrScanStatus === "error" && (
                        <div className="qr-error-state">
                          <div className="qr-error-icon">❌</div>
                          <p className="qr-error-text">
                            Không thể trích xuất thông tin
                          </p>
                          <button
                            onClick={resetQRScan}
                            className="qr-retry-button"
                          >
                            Thử lại
                          </button>
                        </div>
                      )}

                      {qrScanStatus === "success" && cccdData && (
                        <div className="qr-success-state">
                          <div className="qr-success-icon">✅</div>
                          <p className="qr-success-text">Quét thành công!</p>
                          <button
                            onClick={resetQRScan}
                            className="qr-new-scan-button"
                          >
                            Quét ảnh khác
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* CCCD Information Display */}
              {cccdData && (
                <div className="cccd-info-section">
                  <h3 className="cccd-info-title">📋 Thông tin từ CCCD</h3>
                  <div className="cccd-info-grid">
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Họ tên:</span>
                      <span className="cccd-info-value">
                        {cccdData.full_name}
                      </span>
                    </div>
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Ngày sinh:</span>
                      <span className="cccd-info-value">
                        {cccdData.date_of_birth}
                      </span>
                    </div>
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Địa chỉ:</span>
                      <span className="cccd-info-value">
                        {cccdData.address}
                      </span>
                    </div>
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Số CCCD:</span>
                      <span className="cccd-info-value">
                        {cccdData.citizen_id}
                      </span>
                    </div>
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Giới tính:</span>
                      <span className="cccd-info-value">{cccdData.gender}</span>
                    </div>
                    <div className="cccd-info-item">
                      <span className="cccd-info-label">Ngày cấp:</span>
                      <span className="cccd-info-value">
                        {cccdData.issue_date}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
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
