import axios from "axios";
import type {
  APIResponse,
  ImageUploadRequest,
  CCCDSession,
  CCCDExtractedData,
  ConfidenceScores,
  ProcessingStatus,
} from "../types/ocr";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`[OCR API] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[OCR API Error]", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface OCRService {
  uploadImage: (request: ImageUploadRequest) => Promise<APIResponse>;
  processOCR: (
    sessionId: string,
    processBothSides?: boolean
  ) => Promise<APIResponse>;
  getResults: (sessionId: string) => Promise<
    APIResponse<{
      extracted_data?: CCCDExtractedData;
      confidence_scores?: ConfidenceScores;
      processing_status: ProcessingStatus;
      error_message?: string;
      processing_time?: number;
    }>
  >;
  getSessionStatus: (sessionId: string) => Promise<
    APIResponse<{
      processing_status: ProcessingStatus;
      has_front_image: boolean;
      has_back_image: boolean;
      created_at: string;
      updated_at: string;
      expires_at: string;
    }>
  >;
  createSession: (sessionId?: string) => Promise<APIResponse<CCCDSession>>;
  deleteSession: (sessionId: string) => Promise<APIResponse>;
  getServiceStats: () => Promise<APIResponse>;
  healthCheck: () => Promise<{
    status: string;
    cache_connected: boolean;
    ocr_initialized: boolean;
  }>;
}

export const ocrService: OCRService = {
  /**
   * Upload CCCD image (front or back side)
   */
  async uploadImage(request: ImageUploadRequest): Promise<APIResponse> {
    try {
      const response = await api.post("/api/ocr/upload-image", request);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to upload image: ${error}`);
    }
  },

  /**
   * Start OCR processing for a session
   */
  async processOCR(
    sessionId: string,
    processBothSides = true
  ): Promise<APIResponse> {
    try {
      const response = await api.post(`/api/ocr/process/${sessionId}`, null, {
        params: { process_both_sides: processBothSides },
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to start OCR processing: ${error}`);
    }
  },

  /**
   * Get OCR processing results
   */
  async getResults(sessionId: string): Promise<
    APIResponse<{
      extracted_data?: CCCDExtractedData;
      confidence_scores?: ConfidenceScores;
      processing_status: ProcessingStatus;
      error_message?: string;
      processing_time?: number;
    }>
  > {
    try {
      const response = await api.get(`/api/ocr/results/${sessionId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get OCR results: ${error}`);
    }
  },

  /**
   * Get session status
   */
  async getSessionStatus(sessionId: string): Promise<
    APIResponse<{
      processing_status: ProcessingStatus;
      has_front_image: boolean;
      has_back_image: boolean;
      created_at: string;
      updated_at: string;
      expires_at: string;
    }>
  > {
    try {
      const response = await api.get(`/api/ocr/session/${sessionId}/status`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get session status: ${error}`);
    }
  },

  /**
   * Create a new OCR session
   */
  async createSession(sessionId?: string): Promise<APIResponse<CCCDSession>> {
    try {
      const response = await api.post("/api/ocr/session/create", {
        session_id: sessionId,
      });
      return response.data;
    } catch (error) {
      throw new Error(`Failed to create session: ${error}`);
    }
  },

  /**
   * Delete session and all associated data
   */
  async deleteSession(sessionId: string): Promise<APIResponse> {
    try {
      const response = await api.delete(`/api/ocr/session/${sessionId}`);
      return response.data;
    } catch (error) {
      throw new Error(`Failed to delete session: ${error}`);
    }
  },

  /**
   * Get service statistics
   */
  async getServiceStats(): Promise<APIResponse> {
    try {
      const response = await api.get("/api/ocr/stats");
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get service stats: ${error}`);
    }
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{
    status: string;
    cache_connected: boolean;
    ocr_initialized: boolean;
  }> {
    try {
      const response = await api.get("/api/ocr/health");
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error}`);
    }
  },
};

export default ocrService;
