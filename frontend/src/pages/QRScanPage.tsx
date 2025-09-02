import React, { useState } from "react";
import { QRScanner } from "../components/ocr/QRScanner";
import { QRFileUpload } from "../components/ocr/QRFileUpload";
import { identifillService } from "../services/identifillService";
import { Camera, Upload } from "lucide-react";
import type { CCCDExtractedData } from "../types/ocr";
import "./QRScanPage.css";
import "../components/ocr/QRFileUpload.css";

type ScanMethod = "camera" | "upload";

const QRScanPage: React.FC = () => {
  const [extractedData, setExtractedData] = useState<CCCDExtractedData | null>(
    null
  );
  const [scanMethod, setScanMethod] = useState<ScanMethod>("camera");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleResult = (data: CCCDExtractedData) => {
    setExtractedData(data);
    console.log("QR Scan Result:", data);
  };

  const handleError = (error: string) => {
    console.error("QR Scan Error:", error);
  };

  const handleReset = () => {
    setExtractedData(null);
  };

  const handleFileUpload = async (imageData: string) => {
    setIsProcessing(true);
    try {
      // First try normal QR scan
      let result = await identifillService.scanQRCode(imageData);

      // If failed, try enhanced scan
      if (!result.success) {
        result = await identifillService.scanQRCodeEnhanced(imageData);
      }

      if (result.success && result.data) {
        handleResult(result.data);
      } else {
        handleError(result.message || "Không thể đọc QR code từ ảnh này");
      }
    } catch (error) {
      handleError("Lỗi khi xử lý ảnh: " + (error as Error).message);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="qr-scan-page">
      <div className="qr-scan-container">
        {/* Header */}
        <div className="qr-scan-header">
          <div className="header-content">
            <h1 className="main-title">
              <span className="icon">🔍</span>
              QR Scanner CCCD
            </h1>
            <p className="subtitle">
              Quét mã QR trên Căn cước công dân để trích xuất thông tin tự động
            </p>
          </div>

          {/* Status Badge */}
          <div className="status-badge">
            <div className="badge-content">
              <div className="status-indicator active"></div>
              <div className="status-details">
                <span className="speed">⚡ Tốc độ: 2-3 giây</span>
                <span className="accuracy">🎯 Độ chính xác: Cao</span>
                <span className="ease">🔋 Chỉ cần 1 lần quét</span>
              </div>
            </div>
          </div>
        </div>

        {/* Main Scanner Interface */}
        <div className="scanner-section">
          {!extractedData ? (
            <>
              {/* Method Tabs */}
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

              <div className="scanner-instructions">
                <h3>📋 Hướng dẫn sử dụng:</h3>
                {scanMethod === "camera" ? (
                  <ul>
                    <li>🔲 Đặt thẻ CCCD trong khung camera</li>
                    <li>📍 Định vị mã QR ở góc phải dưới thẻ</li>
                    <li>💡 Đảm bảo ánh sáng đủ sáng</li>
                    <li>📏 Khoảng cách 10-15cm từ camera</li>
                  </ul>
                ) : (
                  <ul>
                    <li>📸 Chụp ảnh QR code rõ nét bằng điện thoại</li>
                    <li>🔍 Đảm bảo toàn bộ QR code trong ảnh</li>
                    <li>💡 Ảnh đủ sáng và không bị mờ</li>
                    <li>📁 Chọn file hoặc kéo thả vào khung bên dưới</li>
                  </ul>
                )}
              </div>

              {scanMethod === "camera" ? (
                <QRScanner onResult={handleResult} onError={handleError} />
              ) : (
                <QRFileUpload
                  onFileSelected={handleFileUpload}
                  disabled={isProcessing}
                />
              )}
            </>
          ) : (
            <div className="results-section">
              <div className="success-header">
                <h2>✅ Quét thành công!</h2>
                <button onClick={handleReset} className="reset-button">
                  🔄 Quét lại
                </button>
              </div>

              <div className="extracted-data">
                <div className="data-grid">
                  <div className="data-item">
                    <label>Số CCCD:</label>
                    <span>
                      {extractedData.citizen_id || extractedData.id_number}
                    </span>
                  </div>

                  <div className="data-item">
                    <label>Họ và tên:</label>
                    <span>{extractedData.full_name}</span>
                  </div>

                  <div className="data-item">
                    <label>Ngày sinh:</label>
                    <span>{extractedData.date_of_birth}</span>
                  </div>

                  <div className="data-item">
                    <label>Giới tính:</label>
                    <span>{extractedData.gender}</span>
                  </div>

                  <div className="data-item">
                    <label>Địa chỉ:</label>
                    <span>
                      {extractedData.address || extractedData.residence}
                    </span>
                  </div>

                  <div className="data-item">
                    <label>Ngày cấp:</label>
                    <span>{extractedData.issue_date}</span>
                  </div>

                  {extractedData.old_id && (
                    <div className="data-item">
                      <label>Số CMND cũ:</label>
                      <span>{extractedData.old_id}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Debug Panel (Development only) */}
        {extractedData && typeof window !== "undefined" && (
          <div className="debug-panel">
            <details>
              <summary>🔧 Debug Information</summary>
              <div className="debug-content">
                <pre>{JSON.stringify(extractedData, null, 2)}</pre>
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default QRScanPage;
