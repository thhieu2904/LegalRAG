import React, { useState, useCallback } from "react";
import { CameraComponent } from "./CameraComponent";
import { ServiceTester } from "../debug/ServiceTester";
import { qrScannerAPI } from "../../api/qr-scanner-api";
import {
  QrCode,
  Camera,
  CheckCircle,
  AlertCircle,
  Loader,
  RefreshCcw,
} from "lucide-react";
import type { CCCDData } from "../../api/qr-scanner-api";
import "./QRScanner.css";

interface QRScannerProps {
  onResult?: (data: CCCDData) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const QRScanner: React.FC<QRScannerProps> = ({
  onResult,
  onError,
  className = "",
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scannedData, setScannedData] = useState<CCCDData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  const handleImageCapture = useCallback(
    async (imageData: string) => {
      setIsScanning(true);
      setError(null);

      try {
        console.log("🔍 QR Scanner: Starting image processing...");
        console.log("📏 Image data size:", imageData.length, "characters");

        // Log first few characters to see format
        console.log("📄 Image format:", imageData.substring(0, 50));

        const startTime = Date.now();

        // Use the new unified QR scanning API
        console.log("🔍 Scanning QR code with new API...");
        const result = await qrScannerAPI.scanQRCode(imageData);

        const endTime = Date.now();
        const processingTimeMs = endTime - startTime;
        setProcessingTime(processingTimeMs);

        if (result.success && result.data) {
          console.log("✅ QR scan successful:", result.data);
          setScannedData(result.data);
          setProcessingTime(result.processing_time || processingTimeMs);
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

  const reset = useCallback(() => {
    setScannedData(null);
    setError(null);
    setProcessingTime(null);
  }, []);

  return (
    <div className={`qr-scanner ${className}`}>
      {/* Header */}
      <div className="qr-scanner-header">
        <div className="header-content">
          <div className="title-section">
            <QrCode className="title-icon" />
            <h2>QR Code Scanner</h2>
          </div>
          <div className="service-status">
            <ServiceTester />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="qr-scanner-content">
        {!scannedData ? (
          <>
            {/* Camera Section */}
            <div className="camera-section">
              <div className="camera-header">
                <Camera className="section-icon" />
                <h3>Capture CCCD Image</h3>
              </div>

              <div className="camera-wrapper">
                <CameraComponent
                  onImageCapture={handleImageCapture}
                  onError={handleError}
                  isCapturing={isScanning}
                  captureButtonText={
                    isScanning ? "Processing..." : "Scan QR Code"
                  }
                />
              </div>

              {isScanning && (
                <div className="processing-indicator">
                  <Loader className="spinning" />
                  <span>Processing QR code...</span>
                </div>
              )}

              {error && (
                <div className="error-message">
                  <AlertCircle className="error-icon" />
                  <div className="error-content">
                    <h4>Scanning Failed</h4>
                    <p>{error}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="instructions">
              <h4>📋 Instructions</h4>
              <ul>
                <li>Place your CCCD flat on a well-lit surface</li>
                <li>Ensure the QR code is clearly visible and not blurry</li>
                <li>Avoid shadows or reflections on the card</li>
                <li>Hold the camera steady when capturing</li>
              </ul>
            </div>
          </>
        ) : (
          /* Results Section */
          <div className="results-section">
            <div className="success-header">
              <CheckCircle className="success-icon" />
              <h3>QR Code Scanned Successfully!</h3>
            </div>

            <div className="cccd-data">
              <div className="data-grid">
                <div className="data-item">
                  <label>Citizen ID:</label>
                  <span>{scannedData.citizen_id}</span>
                </div>

                <div className="data-item">
                  <label>Full Name:</label>
                  <span>{scannedData.full_name}</span>
                </div>

                <div className="data-item">
                  <label>Date of Birth:</label>
                  <span>{scannedData.date_of_birth}</span>
                </div>

                <div className="data-item">
                  <label>Gender:</label>
                  <span>{scannedData.gender}</span>
                </div>

                <div className="data-item">
                  <label>Address:</label>
                  <span>{scannedData.address}</span>
                </div>

                <div className="data-item">
                  <label>Issue Date:</label>
                  <span>{scannedData.issue_date}</span>
                </div>

                {scannedData.old_id && (
                  <div className="data-item">
                    <label>Old ID:</label>
                    <span>{scannedData.old_id}</span>
                  </div>
                )}
              </div>

              {processingTime && (
                <div className="processing-time">
                  ⏱️ Processing time: {processingTime}ms
                </div>
              )}
            </div>

            <div className="action-buttons">
              <button onClick={reset} className="reset-button">
                <RefreshCcw className="button-icon" />
                Scan Another
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
