/**
 * 📷 OCR SERVICE API - TẤT CẢ CALLS ĐẾN OCR SERVICE (PORT 8001)
 * CCCD recognition, image processing
 */
import { ocrAPI } from "./axios-config";

// ========================================
// OCR API - Cho OCRPage
// ========================================
export interface CCCDData {
  id: string;
  fullName: string;
  dateOfBirth: string;
  placeOfBirth: string;
  address: string;
  idNumber: string;
  issueDate: string;
  expiryDate?: string;
  gender?: string;
  nationality?: string;
}

export interface OCRResult {
  success: boolean;
  data: CCCDData;
  confidence: number;
  processTime: number;
  extractedAt: string;
}

export interface OCRHistory {
  id: string;
  filename: string;
  extractedData: CCCDData;
  confidence: number;
  processedAt: string;
  status: "completed" | "failed" | "processing";
}

export const ocrAPI_Service = {
  // Xử lý ảnh CCCD
  processImage: async (imageFile: File): Promise<OCRResult> => {
    try {
      const formData = new FormData();
      formData.append("image", imageFile);

      const response = await ocrAPI.post("/ocr/process", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return response.data;
    } catch (error) {
      console.error("OCR Process API Error:", error);
      throw error;
    }
  },

  // Upload và xử lý từ URL
  processImageFromURL: async (imageUrl: string): Promise<OCRResult> => {
    try {
      const response = await ocrAPI.post("/ocr/process-url", { url: imageUrl });
      return response.data;
    } catch (error) {
      console.error("OCR Process URL API Error:", error);
      throw error;
    }
  },

  // Lấy lịch sử xử lý OCR
  getOCRHistory: async (): Promise<OCRHistory[]> => {
    try {
      const response = await ocrAPI.get("/ocr/history");
      return response.data;
    } catch (error) {
      console.error("OCR History API Error:", error);
      throw error;
    }
  },

  // Lấy chi tiết một kết quả OCR
  getOCRResult: async (id: string): Promise<OCRResult> => {
    try {
      const response = await ocrAPI.get(`/ocr/result/${id}`);
      return response.data;
    } catch (error) {
      console.error("OCR Result API Error:", error);
      throw error;
    }
  },

  // Xóa kết quả OCR
  deleteOCRResult: async (id: string): Promise<{ message: string }> => {
    try {
      const response = await ocrAPI.delete(`/ocr/result/${id}`);
      return response.data;
    } catch (error) {
      console.error("Delete OCR Result API Error:", error);
      throw error;
    }
  },

  // Kiểm tra trạng thái OCR service
  getServiceStatus: async () => {
    try {
      const response = await ocrAPI.get("/health");
      return response.data;
    } catch (error) {
      console.error("OCR Service Status API Error:", error);
      throw error;
    }
  },

  // Lấy thống kê OCR service
  getOCRStats: async () => {
    try {
      const response = await ocrAPI.get("/ocr/stats");
      return response.data;
    } catch (error) {
      console.error("OCR Stats API Error:", error);
      throw error;
    }
  },

  // Validate CCCD data
  validateCCCDData: async (data: Partial<CCCDData>) => {
    try {
      const response = await ocrAPI.post("/ocr/validate", data);
      return response.data;
    } catch (error) {
      console.error("CCCD Validation API Error:", error);
      throw error;
    }
  },
};
