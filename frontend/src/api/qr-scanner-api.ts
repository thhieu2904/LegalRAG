/**
 * 📷 CCCD SCANNER API - TẤT CẢ CALLS ĐẾN IDENTIFILL SERVICE (PORT 8002)
 * CCCD scanning for Vietnamese ID cards
 */
import { identifillAPI } from "./axios-config";

// ========================================
// Interfaces
// ========================================
export interface CCCDData {
  scan_cccd: string;
  scan_cmnd?: string;
  scan_ho_ten: string;
  scan_ngay_sinh: string;
  scan_gioi_tinh: string;
  scan_dia_chi: string;
  scan_ngay_cap: string;
}

export interface CCCDScanResult {
  success: boolean;
  data?: CCCDData;
  message?: string;
  processing_time?: number;
  confidence?: number;
}

export type ScanMode = "qr";

// ========================================
// CCCD Scanner API Service
// ========================================
export const cccdScannerAPI = {
  // Quét CCCD từ ảnh
  scanCCCD: async (
    imageData: string,
    scanMode: ScanMode = "qr"
  ): Promise<CCCDScanResult> => {
    try {
      const response = await identifillAPI.post("/api/v1/cccd/scan", {
        image_data: imageData,
        scan_mode: scanMode,
      });
      return response.data;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      if (err.response?.data) {
        // Nếu server trả về lỗi được format
        return {
          success: false,
          message: err.response.data.detail || "Không thể quét CCCD",
        };
      }
      console.error("CCCD Scan API Error:", error);
      return {
        success: false,
        message: "Lỗi kết nối đến máy chủ",
      };
    }
  },

  // Kiểm tra trạng thái CCCD service
  getServiceStatus: async (): Promise<{ message: string; status: string }> => {
    try {
      const response = await identifillAPI.get("/api/v1/cccd/test");
      return response.data;
    } catch (error) {
      console.error("CCCD Scanner Service Status API Error:", error);
      throw error;
    }
  },

  // Phát hiện thẻ CCCD trong ảnh
  detectCard: async (
    imageData: string,
    autoCrop: boolean = true
  ): Promise<{
    success: boolean;
    card_detected: boolean;
    cropped_image?: string;
    confidence?: number;
    message?: string;
  }> => {
    try {
      const response = await identifillAPI.post("/api/v1/cccd/detect", {
        image_data: imageData,
        auto_crop: autoCrop,
      });
      return response.data;
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      if (err.response?.data) {
        return {
          success: false,
          card_detected: false,
          message: err.response.data.detail || "Không thể phát hiện thẻ CCCD",
        };
      }
      console.error("Card Detection API Error:", error);
      return {
        success: false,
        card_detected: false,
        message: "Lỗi kết nối đến máy chủ",
      };
    }
  },
};
