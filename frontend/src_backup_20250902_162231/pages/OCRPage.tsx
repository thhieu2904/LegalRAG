import React, { useState } from "react";
import { OCRInterface } from "../components/ocr/OCRInterface";
import type { CCCDExtractedData } from "../types/ocr";

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
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="container mx-auto px-4">
        <OCRInterface onResult={handleResult} onError={handleError} />

        {/* Debug panel (optional, can be removed in production) */}
        {extractedData && (
          <div className="mt-8 max-w-4xl mx-auto">
            <details className="bg-white rounded-lg shadow p-6">
              <summary className="cursor-pointer font-semibold text-gray-700">
                Debug: Latest Extracted Data
              </summary>
              <pre className="mt-4 text-sm bg-gray-100 p-4 rounded overflow-auto">
                {JSON.stringify(extractedData, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

export default OCRPage;
