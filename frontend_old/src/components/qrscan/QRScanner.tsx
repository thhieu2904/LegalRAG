import React, { useState, useCallback } from "react";
import { CameraComponent } from "./CameraComponent";
import { QRFileUpload } from "./QRFileUpload";
import { cccdScannerAPI } from "../../api/qr-scanner-api";
import { AlertCircle, Loader, Camera, Upload } from "lucide-react";
import type { CCCDData } from "../../api/qr-scanner-api";
import "./QRScanner.css";

interface QRScannerProps {
  onResult?: (data: CCCDData) => void;
  onError?: (error: string) => void;
  className?: string;
}

type ScanMode = "camera" | "upload";

export const QRScanner: React.FC<QRScannerProps> = ({
  onResult,
  onError,
  className = "",
}) => {
  const [scanMode, setScanMode] = useState<ScanMode>("upload");
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleImageCapture = useCallback(
    async (imageData: string) => {
      setIsScanning(true);
      setError(null);

      try {
        console.log("🔍 QR Scanner: Starting image processing...");
        console.log("📏 Image data size:", imageData.length, "characters");

        // Log first few characters to see format
        console.log("📄 Image format:", imageData.substring(0, 50));

        // Use the new unified QR scanning API
        console.log("🔍 Scanning QR code with new API...");
        const result = await cccdScannerAPI.scanCCCD(imageData);

        if (result.success && result.data) {
          console.log("✅ QR scan successful:", result.data);
          onResult?.(result.data);
        } else {
          const errorMessage = result.message || "Failed to scan QR code";
          // More user-friendly error messages
          let friendlyMessage = errorMessage;
          if (errorMessage.includes("No QR code found")) {
            friendlyMessage =
              "No QR code detected in the image. Please ensure the QR code on your CCCD is clearly visible and try again.";
          } else if (errorMessage.includes("Invalid QR code format")) {
            friendlyMessage =
              "QR code detected but not in CCCD format. Please scan the QR code on your CCCD.";
          }

          setError(friendlyMessage);
          onError?.(friendlyMessage);
        }
      } catch (err) {
        let errorMessage = "Unknown error";
        if (err instanceof Error) {
          if (err.message.includes("Request failed")) {
            errorMessage =
              "Connection to QR scanner service failed. Please check if the service is running.";
          } else if (err.message.includes("Network Error")) {
            errorMessage =
              "Network error. Please check your internet connection.";
          } else {
            errorMessage = err.message;
          }
        }

        console.error("QR Scanner Error:", err);
        setError(errorMessage);
        onError?.(errorMessage);
      } finally {
        setIsScanning(false);
      }
    },
    [onResult, onError]
  );

  const handleError = useCallback(
    (errorMessage: string) => {
      setError(errorMessage);
      onError?.(errorMessage);
    },
    [onError]
  );

  return (
    <div className={`qr-scanner ${className}`}>
      {/* Mode Selector Tabs */}
      <div className="scan-mode-tabs">
        <button
          className={`mode-tab ${scanMode === "upload" ? "active" : ""}`}
          onClick={() => {
            setScanMode("upload");
            setError(null);
          }}
          disabled={isScanning}
        >
          <Upload className="tab-icon" />
          <span>Tải ảnh lên</span>
        </button>
        <button
          className={`mode-tab ${scanMode === "camera" ? "active" : ""}`}
          onClick={() => {
            setScanMode("camera");
            setError(null);
          }}
          disabled={isScanning}
        >
          <Camera className="tab-icon" />
          <span>Quét bằng Camera</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="qr-scanner-content">
        {/* Camera Section - Visible when camera mode */}
        {scanMode === "camera" && (
          <div className="camera-section">
            <div className="camera-wrapper">
              <CameraComponent
                onImageCapture={handleImageCapture}
                onError={handleError}
                isCapturing={isScanning}
                captureButtonText={isScanning ? "Đang xử lý..." : "Chụp ảnh"}
              />
            </div>
          </div>
        )}

        {/* Upload Section - Visible when upload mode */}
        {scanMode === "upload" && (
          <div className="upload-section">
            <QRFileUpload
              onFileSelected={handleImageCapture}
              disabled={isScanning}
            />
          </div>
        )}

        {/* Processing Indicator */}
        {isScanning && (
          <div className="processing-indicator">
            <Loader className="spinning" />
            <span>Đang xử lý QR code...</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <AlertCircle className="error-icon" />
            <div className="error-content">
              <h4>Quét thất bại</h4>
              <p>{error}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
