import React, { useState } from "react";
import { OCRInterface } from "../components/ocr/OCRInterface";
import type { CCCDExtractedData } from "../types/ocr";
import "./OCRPage.css";

const OCRPage: React.FC = () => {
  const [extractedData, setExtractedData] = useState<CCCDExtractedData | null>(
    null
  );

  const handleResult = (data: CCCDExtractedData) => {
    setExtractedData(data);
    console.log("OCR Result:", data);
  };

  const handleError = (error: string) => {
    console.error("OCR Error:", error);
    // You can add toast notification here
  };

  return (
    <div className="ocr-page">
      <div className="ocr-container">
        <div className="ocr-header">
          <h1>📄 OCR Service</h1>
          <p>Trích xuất thông tin từ ảnh Căn cước công dân tự động</p>
        </div>

        <div className="ocr-interface-container">
          <OCRInterface onResult={handleResult} onError={handleError} />
        </div>

        {/* Debug panel (optional, can be removed in production) */}
        {extractedData && (
          <div className="ocr-debug-panel">
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
