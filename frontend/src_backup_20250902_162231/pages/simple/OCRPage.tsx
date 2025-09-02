/**
 * 📷 OCR PAGE - GIAO TIẾP VỚI OCR SERVICE
 * Trang xử lý OCR CCCD riêng biệt
 */
import React, { useState, useRef } from "react";
import {
  Upload,
  CreditCard,
  Eye,
  Download,
  Trash2,
  Camera,
} from "lucide-react";
import { ocrAPI_Service } from "../../api";
import type { OCRResult, CCCDData } from "../../api";

const OCRPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingHistory, setProcessingHistory] = useState<OCRResult[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);

      // Create preview URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleProcessImage = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);

    try {
      const result = await ocrAPI_Service.processImage(selectedFile);
      setOcrResult(result);

      // Add to history
      setProcessingHistory((prev) => [result, ...prev.slice(0, 4)]);

      console.log("OCR Result:", result);
    } catch (error) {
      console.error("OCR Processing Error:", error);
      setError("Không thể xử lý ảnh. Vui lòng thử lại với ảnh khác.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClearAll = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setOcrResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatCCCDData = (data: CCCDData) => {
    return [
      { label: "Họ và tên", value: data.fullName },
      { label: "Số CCCD", value: data.idNumber },
      { label: "Ngày sinh", value: data.dateOfBirth },
      { label: "Giới tính", value: data.gender || "N/A" },
      { label: "Quốc tịch", value: data.nationality || "Việt Nam" },
      { label: "Nơi sinh", value: data.placeOfBirth },
      { label: "Địa chỉ", value: data.address },
      { label: "Ngày cấp", value: data.issueDate },
      { label: "Ngày hết hạn", value: data.expiryDate || "Không có" },
    ];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-6xl mx-auto flex items-center gap-3">
          <CreditCard className="w-6 h-6 text-blue-600" />
          <h1 className="text-xl font-semibold text-gray-800">
            OCR CCCD Service
          </h1>
          <span className="text-sm text-gray-500">
            • OCR Service (Port 8001)
          </span>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column - Upload & Preview */}
        <div className="space-y-4">
          {/* Upload Area */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Tải ảnh CCCD
            </h2>

            {!selectedFile ? (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <Camera className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Chọn ảnh CCCD để xử lý OCR</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Chọn ảnh
                </button>
                <p className="text-sm text-gray-500 mt-2">
                  Hỗ trợ: JPG, PNG, WEBP (tối đa 10MB)
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative">
                  <img
                    src={previewUrl || ""}
                    alt="Preview"
                    className="w-full h-64 object-contain bg-gray-100 rounded-lg"
                  />
                </div>
                <div className="flex justify-between items-center">
                  <p className="text-sm text-gray-600">
                    {selectedFile.name} ({Math.round(selectedFile.size / 1024)}
                    KB)
                  </p>
                  <button
                    onClick={handleClearAll}
                    className="px-3 py-1 text-red-600 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Process Button */}
          {selectedFile && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <button
                onClick={handleProcessImage}
                disabled={isProcessing}
                className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Đang xử lý...
                  </>
                ) : (
                  <>
                    <Eye className="w-4 h-4" />
                    Xử lý OCR
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Right Column - Results */}
        <div className="space-y-4">
          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* OCR Results */}
          {ocrResult && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                  <CreditCard className="w-5 h-5" />
                  Kết quả OCR
                </h2>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Độ chính xác:</span>
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm font-medium">
                    {Math.round(ocrResult.confidence * 100)}%
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {formatCCCDData(ocrResult.data).map((item, index) => (
                  <div
                    key={index}
                    className="flex border-b border-gray-100 pb-2"
                  >
                    <div className="w-1/3 text-sm font-medium text-gray-600">
                      {item.label}:
                    </div>
                    <div className="w-2/3 text-sm text-gray-800">
                      {item.value || "N/A"}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-500">
                Thời gian xử lý: {ocrResult.processTime}ms | Xử lý lúc:{" "}
                {new Date(ocrResult.extractedAt).toLocaleString("vi-VN")}
              </div>

              {/* Actions */}
              <div className="mt-4 flex gap-2">
                <button className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-1">
                  <Download className="w-4 h-4" />
                  Xuất JSON
                </button>
                <button className="px-3 py-2 bg-gray-600 text-white rounded text-sm hover:bg-gray-700 flex items-center gap-1">
                  <Download className="w-4 h-4" />
                  Xuất PDF
                </button>
              </div>
            </div>
          )}

          {/* Processing History */}
          {processingHistory.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-md font-semibold text-gray-800 mb-4">
                Lịch sử xử lý gần đây
              </h3>
              <div className="space-y-3">
                {processingHistory.map((result, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded border text-sm"
                  >
                    <div className="font-medium">
                      {result.data.fullName || "N/A"}
                    </div>
                    <div className="text-gray-600">
                      ID: {result.data.idNumber || "N/A"} | Độ chính xác:{" "}
                      {Math.round(result.confidence * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(result.extractedAt).toLocaleString("vi-VN")}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Features */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-md font-semibold text-gray-800 mb-4">
              Tính năng OCR
            </h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• Nhận diện CCCD Việt Nam (mặt trước)</li>
              <li>• Trích xuất thông tin tự động</li>
              <li>• Hỗ trợ nhiều định dạng ảnh</li>
              <li>• Độ chính xác cao với AI</li>
              <li>• Xuất dữ liệu JSON/PDF</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OCRPage;
