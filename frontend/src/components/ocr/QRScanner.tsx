import React, { useState, useCallback } from "react";
import { CameraComponent } from "./CameraComponent";
import { ServiceTester } from "../debug/ServiceTester";
import { identifillService } from "../../services/identifillService";
import {
  QrCode,
  Camera,
  CheckCircle,
  AlertCircle,
  Loader,
  RefreshCcw,
} from "lucide-react";
import type { CCCDExtractedData } from "../../types/ocr";

interface QRScannerProps {
  onResult?: (data: CCCDExtractedData) => void;
  onError?: (error: string) => void;
  className?: string;
}

export const QRScanner: React.FC<QRScannerProps> = ({
  onResult,
  onError,
  className = "",
}) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scannedData, setScannedData] = useState<CCCDExtractedData | null>(
    null
  );
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

        // First try normal QR scan
        console.log("🔍 Trying normal QR scan...");
        let result = await identifillService.scanQRCode(imageData);

        // If failed, try enhanced scan
        if (!result.success) {
          console.log("❌ Normal scan failed, trying enhanced scan...");
          result = await identifillService.scanQRCodeEnhanced(imageData);
        }

        if (result.success && result.data) {
          console.log("✅ QR scan successful:", result.data);
          setScannedData(result.data);
          setProcessingTime(result.processing_time || null);
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
          } else {
            errorMessage = err.message;
          }
        }
        setError(errorMessage);
        onError?.(errorMessage);
      } finally {
        setIsScanning(false);
      }
    },
    [onResult, onError]
  );

  const resetScanner = useCallback(() => {
    setScannedData(null);
    setError(null);
    setProcessingTime(null);
  }, []);

  return (
    <div className={`max-w-4xl mx-auto p-6 ${className}`}>
      {/* Service Connection Tester */}
      <ServiceTester />

      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center mb-4">
          <QrCode className="w-12 h-12 text-blue-600 mr-3" />
          <h1 className="text-3xl font-bold text-gray-800">QR Code Scanner</h1>
        </div>
        <p className="text-gray-600">
          Scan QR code on your CCCD to extract information instantly
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-100 border border-red-300 rounded-lg flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-red-800 font-medium">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {!scannedData ? (
          <div>
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Camera className="w-5 h-5 mr-2" />
              Scan QR Code on CCCD
            </h2>

            <div className="mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <h3 className="font-medium text-blue-800 mb-2">
                  📋 Instructions:
                </h3>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>
                    • <strong>Position the QR code</strong> on your CCCD clearly
                    in the camera view
                  </li>
                  <li>
                    • <strong>Ensure good lighting</strong> - avoid shadows on
                    the QR code
                  </li>
                  <li>
                    • <strong>Hold steady</strong> - keep the camera stable for
                    clear capture
                  </li>
                  <li>
                    • <strong>QR code location</strong>: Usually on the bottom
                    right of front side
                  </li>
                  <li>
                    • <strong>Distance</strong>: Hold 10-15cm away from the card
                  </li>
                </ul>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <h3 className="font-medium text-amber-800 mb-2">💡 Tips:</h3>
                <ul className="text-sm text-amber-700 space-y-1">
                  <li>
                    • If no QR code is found, try adjusting the angle or
                    lighting
                  </li>
                  <li>
                    • Make sure you're scanning the <strong>front side</strong>{" "}
                    of the CCCD
                  </li>
                  <li>• Clean the camera lens if the image appears blurry</li>
                </ul>
              </div>
            </div>

            <CameraComponent
              onCapture={handleImageCapture}
              onError={(error) => setError(error)}
            />

            {isScanning && (
              <div className="mt-6 flex items-center justify-center space-x-2 text-blue-600">
                <Loader className="w-5 h-5 animate-spin" />
                <span>Scanning QR code...</span>
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
                QR Code Scanned Successfully
              </h2>
              <button
                onClick={resetScanner}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
              >
                <RefreshCcw className="w-4 h-4" />
                <span>Scan Another</span>
              </button>
            </div>

            {processingTime && (
              <div className="mb-4 text-sm text-gray-600">
                Processing completed in {processingTime.toFixed(2)} seconds
              </div>
            )}

            {/* Display extracted data */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Citizen ID
                  </label>
                  <p className="text-lg font-mono">{scannedData.citizen_id}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <p className="text-lg">{scannedData.full_name}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth
                  </label>
                  <p className="text-lg">{scannedData.date_of_birth}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender
                  </label>
                  <p className="text-lg">{scannedData.gender}</p>
                </div>
              </div>

              <div className="space-y-4">
                {scannedData.old_id && (
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Old ID (CMND)
                    </label>
                    <p className="text-lg font-mono">{scannedData.old_id}</p>
                  </div>
                )}

                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <p className="text-lg">{scannedData.address}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Issue Date
                  </label>
                  <p className="text-lg">{scannedData.issue_date}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
