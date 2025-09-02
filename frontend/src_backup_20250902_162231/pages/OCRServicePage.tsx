import React, { useState, useCallback } from "react";
import { CreditCard, Zap, Shield, Clock, CheckCircle } from "lucide-react";
import { OCRInterface } from "../components/ocr/OCRInterface";
import type { CCCDExtractedData } from "../types/ocr";

const OCRServicePage: React.FC = () => {
  const [processingHistory, setProcessingHistory] = useState<
    CCCDExtractedData[]
  >([]);

  const handleOCRResult = useCallback((data: CCCDExtractedData) => {
    setProcessingHistory((prev) => [data, ...prev.slice(0, 4)]); // Keep last 5 results
  }, []);

  const handleOCRError = useCallback((error: string) => {
    console.error("OCR Processing Error:", error);
  }, []);

  const features = [
    {
      icon: <CreditCard className="w-6 h-6" />,
      title: "CCCD Recognition",
      description:
        "Nhận dạng chính xác thông tin từ căn cước công dân Việt Nam",
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Fast Processing",
      description: "Xử lý nhanh chóng với CPU-optimized VietOCR engine",
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "Secure & Private",
      description: "Dữ liệu được bảo mật và tự động xóa sau 2 giờ",
    },
    {
      icon: <Clock className="w-6 h-6" />,
      title: "Real-time Results",
      description: "Theo dõi tiến trình xử lý theo thời gian thực",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                <CreditCard className="w-8 h-8 text-blue-600" />
                OCR Service
              </h1>
              <p className="text-gray-600 mt-1">
                Vietnamese CCCD Recognition Microservice
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Service Running on Port 8001
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-blue-600 mb-4">{feature.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-2">
                {feature.title}
              </h3>
              <p className="text-gray-600 text-sm">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Main OCR Interface */}
        <div className="max-w-6xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5" />
                CCCD Recognition Interface
              </h2>
              <p className="text-blue-100 text-sm mt-1">
                Upload images of Vietnamese citizen ID card for automatic data
                extraction
              </p>
            </div>

            <div className="p-6">
              <OCRInterface
                onResult={handleOCRResult}
                onError={handleOCRError}
                className="w-full"
              />
            </div>
          </div>

          {/* Processing History */}
          {processingHistory.length > 0 && (
            <div className="mt-8">
              <div className="bg-white rounded-xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    Processing History
                  </h3>
                  <p className="text-gray-600 text-sm mt-1">
                    Recent OCR processing results (last 5 sessions)
                  </p>
                </div>

                <div className="p-6">
                  <div className="space-y-4">
                    {processingHistory.map((result, index) => (
                      <div
                        key={index}
                        className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                            <span className="font-medium text-gray-900">
                              {result.full_name || "N/A"}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date().toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                          <div>
                            <span className="text-gray-500">ID:</span>
                            <span className="ml-1 font-mono">
                              {result.id_number || "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">DOB:</span>
                            <span className="ml-1">
                              {result.date_of_birth || "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Gender:</span>
                            <span className="ml-1">
                              {result.gender || "N/A"}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Nationality:</span>
                            <span className="ml-1">
                              {result.nationality || "N/A"}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Service Info Footer */}
      <div className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">CPU</div>
              <div className="text-gray-600">Optimized Processing</div>
              <div className="text-sm text-gray-500 mt-1">
                No GPU required, efficient CPU-only processing
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">2H</div>
              <div className="text-gray-600">Session Expiry</div>
              <div className="text-sm text-gray-500 mt-1">
                Automatic cleanup for privacy protection
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">API</div>
              <div className="text-gray-600">RESTful Interface</div>
              <div className="text-sm text-gray-500 mt-1">
                <a
                  href="http://localhost:8001/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  View API Documentation
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OCRServicePage;
