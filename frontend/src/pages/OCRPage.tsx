import React, { useState } from "react";
import { QRScanner } from "../components/qrscan/QRScanner";
import type { CCCDExtractedData } from "../types/ocr";
import "./OCRPage.css";

const OCRPage: React.FC = () => {
  const [extractedData, setExtractedData] = useState<CCCDExtractedData | null>(
    null
  );

  const handleResult = (data: CCCDExtractedData) => {
    setExtractedData(data);
    console.log("Scan Result:", data);
  };

  const handleError = (error: string) => {
    console.error("Scan Error:", error);
    // You can add toast notification here
  };

  return (
    <div className="ocr-page">
      <div className="ocr-container">
        <div className="ocr-header">
          <h1>� QR Scanner Service</h1>
          <p>Trích xuất thông tin từ QR code trên Căn cước công dân</p>

          <div className="mt-4 text-center">
            <div className="inline-flex items-center justify-center space-x-2 text-sm bg-green-100 text-green-800 px-4 py-2 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>
                ⚡ Nhanh chóng (2-3s) | 🎯 Chính xác cao | 🔋 Chỉ cần 1 lần scan
              </span>
            </div>
          </div>
        </div>

        <div className="ocr-interface-container mt-8">
          <QRScanner onResult={handleResult} onError={handleError} />
        </div>

        {/* Debug panel (optional, can be removed in production) */}
        {extractedData && (
          <div className="ocr-debug-panel mt-8">
            <details>
              <summary className="ocr-debug-summary">
                🔍 Debug: Latest Extracted Data
              </summary>
              <div className="ocr-debug-content">
                <pre className="ocr-debug-json">
                  {JSON.stringify(extractedData, null, 2)}
                </pre>
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default OCRPage;
