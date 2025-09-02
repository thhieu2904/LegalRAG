import axios from "axios";
import type { CCCDExtractedData } from "../types/ocr";

// Create axios instance for identifill service
const identifillAPI = axios.create({
  baseURL: "http://localhost:8002",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface QRScanRequest {
  image_data: string;
  scan_mode: "qr" | "ocr" | "hybrid";
}

export interface QRScanResponse {
  success: boolean;
  data?: CCCDExtractedData;
  message?: string;
  processing_time?: number;
  confidence?: number;
}

export interface CardDetectionRequest {
  image_data: string;
  auto_crop: boolean;
}

export interface CardDetectionResponse {
  success: boolean;
  card_detected: boolean;
  cropped_image?: string;
  confidence?: number;
  message?: string;
}

class IdentifillService {
  private baseURL = "http://localhost:8002/api/v1";

  /**
   * Scan QR code from CCCD image
   */
  async scanQRCode(imageData: string): Promise<QRScanResponse> {
    try {
      const response = await identifillAPI.post<QRScanResponse>(
        `/api/v1/qr/scan`,
        {
          image_data: imageData,
          scan_mode: "qr",
        } as QRScanRequest
      );

      // Map QR data to CCCDExtractedData format
      if (response.data.success && response.data.data) {
        response.data.data = this.mapQRDataToCCCD(response.data.data);
      }

      return response.data;
    } catch (error) {
      console.error("Error scanning QR code:", error);
      return {
        success: false,
        message: "Failed to scan QR code",
      };
    }
  }

  /**
   * Scan QR code with image enhancement
   */
  async scanQRCodeEnhanced(imageData: string): Promise<QRScanResponse> {
    try {
      const response = await identifillAPI.post<QRScanResponse>(
        `/api/v1/qr/scan-enhanced`,
        {
          image_data: imageData,
          scan_mode: "qr",
        } as QRScanRequest
      );

      // Map QR data to CCCDExtractedData format
      if (response.data.success && response.data.data) {
        response.data.data = this.mapQRDataToCCCD(response.data.data);
      }

      return response.data;
    } catch (error) {
      console.error("Error scanning QR code (enhanced):", error);
      return {
        success: false,
        message: "Failed to scan QR code with enhancement",
      };
    }
  }

  /**
   * Detect and optionally crop ID card from image
   */
  async detectCard(
    imageData: string,
    autoCrop: boolean = true
  ): Promise<CardDetectionResponse> {
    try {
      const response = await identifillAPI.post<CardDetectionResponse>(
        `${this.baseURL}/card/detect`,
        {
          image_data: imageData,
          auto_crop: autoCrop,
        } as CardDetectionRequest
      );

      return response.data;
    } catch (error) {
      console.error("Error detecting card:", error);
      return {
        success: false,
        card_detected: false,
        message: "Failed to detect card",
      };
    }
  }

  /**
   * Test if identifill service is available
   */
  async testConnection(): Promise<boolean> {
    try {
      const response = await identifillAPI.get(`/api/v1/qr/test`);
      return response.data.status === "healthy";
    } catch (error) {
      console.error("Identifill service connection failed:", error);
      return false;
    }
  }

  /**
   * Map QR data format to CCCD format for consistency
   */
  private mapQRDataToCCCD(qrData: CCCDExtractedData): CCCDExtractedData {
    return {
      // Map QR fields to CCCD fields
      id_number: qrData.citizen_id,
      citizen_id: qrData.citizen_id,
      old_id: qrData.old_id,
      full_name: qrData.full_name,
      date_of_birth: qrData.date_of_birth,
      gender: qrData.gender,
      address: qrData.address,
      residence: qrData.address, // Map address to residence for compatibility
      issue_date: qrData.issue_date,
    };
  }
}

export const identifillService = new IdentifillService();
