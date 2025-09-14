/**
 * IntegratedQRScanner - Component chuyên dụng cho IntegratedFormPage
 * Layout: 1 cột 2 hàng (Camera trên + Info dưới)
 * Thiết kế đơn giản, tập trung vào chức năng
 */
import React, { useState, useCallback } from "react";
import { CameraComponent } from "../qrscan/CameraComponent";
import { Camera, Upload, Loader, AlertCircle } from "lucide-react";
import { cccdScannerAPI } from "../../api/qr-scanner-api";
import type { CCCDData } from "../../api/qr-scanner-api";
import "./IntegratedQRScanner.css";

interface IntegratedQRScannerProps {
  onResult?: (data: CCCDData) => void;
  onError?: (error: string) => void;
  cccdData?: CCCDData | null;
  onReset?: () => void;
}

export const IntegratedQRScanner: React.FC<IntegratedQRScannerProps> = ({
  onResult,
  onError,
  cccdData,
  onReset,
}) => {
  const [scanMethod, setScanMethod] = useState<"camera" | "upload">("camera");
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Xử lý quét từ camera
  const handleCameraCapture = useCallback(
    async (imageData: string) => {
      setIsScanning(true);
      setError(null);

      try {
        console.log("🔍 IntegratedCCCDScanner: Starting CCCD scan...");
        const result = await cccdScannerAPI.scanCCCD(imageData);

        if (result.success && result.data) {
          console.log("✅ CCCD scan successful:", result.data);
          onResult?.(result.data);
        } else {
          const errorMessage = result.message || "Không thể quét CCCD";
          setError(errorMessage);
          onError?.(errorMessage);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Lỗi không xác định";
        console.error("CCCD Scanner Error:", err);
        setError(errorMessage);
        onError?.(errorMessage);
      } finally {
        setIsScanning(false);
      }
    },
    [onResult, onError]
  );

  // Xử lý upload ảnh
  const handleImageUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsScanning(true);
    setError(null);

    try {
      // Convert file to base64
      const base64Data = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      // Use the QR scanner API service instead of direct fetch
      const result = await cccdScannerAPI.scanCCCD(base64Data);

      if (result.success && result.data) {
        onResult?.(result.data);
      } else {
        throw new Error(result.message || "CCCD scan failed");
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Lỗi upload";
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCameraError = useCallback(
    (errorMessage: string) => {
      setError(errorMessage);
      onError?.(errorMessage);
    },
    [onError]
  );

  return (
    <div className="integrated-qr-scanner">
      {/* Header */}
      <div className="scanner-header">
        <h2 className="scanner-title">📱 Truy xuất CCCD</h2>
        <p className="scanner-subtitle">
          Quét trực tiếp từ camera hoặc tải ảnh CCCD để tự động điền thông tin
        </p>
      </div>

      {/* Method Tabs */}
      <div className="method-tabs">
        <button
          onClick={() => setScanMethod("camera")}
          className={`method-tab ${scanMethod === "camera" ? "active" : ""}`}
        >
          <Camera size={18} />
          <span>Camera</span>
        </button>
        <button
          onClick={() => setScanMethod("upload")}
          className={`method-tab ${scanMethod === "upload" ? "active" : ""}`}
        >
          <Upload size={18} />
          <span>Tải ảnh</span>
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="scanner-content">
        {/* Scan Area */}
        <div className="scan-area">
          {scanMethod === "camera" ? (
            <div className="camera-container">
              <CameraComponent
                onImageCapture={handleCameraCapture}
                onError={handleCameraError}
                isCapturing={isScanning}
                captureButtonText={
                  isScanning ? "Đang xử lý..." : "Đang quét..."
                }
              />
            </div>
          ) : (
            <div className="upload-container">
              <div className={`upload-zone ${isScanning ? "processing" : ""}`}>
                {!isScanning ? (
                  <>
                    <div className="upload-icon">📷</div>
                    <p className="upload-text">Chọn ảnh CCCD để quét</p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleImageUpload}
                      className="upload-input"
                      id="upload-input"
                    />
                    <label htmlFor="upload-input" className="upload-button">
                      Chọn ảnh
                    </label>
                  </>
                ) : (
                  <div className="processing-state">
                    <Loader className="spinning" />
                    <p>Đang xử lý...</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="error-display">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>

        {/* Info Area */}
        {cccdData && (
          <div className="info-area">
            <div className="info-header">
              <h3 className="info-title">📋 Thông tin từ CCCD</h3>
              {onReset && (
                <button onClick={onReset} className="reset-button">
                  Quét lại
                </button>
              )}
            </div>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Họ tên:</span>
                <span className="info-value">{cccdData.scan_ho_ten}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Ngày sinh:</span>
                <span className="info-value">{cccdData.scan_ngay_sinh}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Địa chỉ:</span>
                <span className="info-value">{cccdData.scan_dia_chi}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Số CCCD:</span>
                <span className="info-value">{cccdData.scan_cccd}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Giới tính:</span>
                <span className="info-value">{cccdData.scan_gioi_tinh}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Ngày cấp:</span>
                <span className="info-value">{cccdData.scan_ngay_cap}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
