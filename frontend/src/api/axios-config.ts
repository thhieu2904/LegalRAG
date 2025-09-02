/**
 * 🔧 AXIOS CONFIGURATION - CẤU HÌNH TẬP TRUNG
 * Tất cả các service sẽ sử dụng config này
 */
import axios from "axios";

// Cấu hình cho RAG Service (Port 8000)
export const ragAPI = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Cấu hình cho OCR Service (Port 8001)
export const ocrAPI = axios.create({
  baseURL: "http://localhost:8001",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - Thêm token nếu cần
ragAPI.interceptors.request.use(
  (config) => {
    // Thêm token vào header nếu có
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(
      `🚀 RAG API Call: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("❌ RAG API Request Error:", error);
    return Promise.reject(error);
  }
);

ocrAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(
      `🚀 OCR API Call: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => {
    console.error("❌ OCR API Request Error:", error);
    return Promise.reject(error);
  }
);

// Response interceptor - Xử lý lỗi tập trung
ragAPI.interceptors.response.use(
  (response) => {
    console.log(
      `✅ RAG API Success: ${response.status} ${response.config.url}`
    );
    return response;
  },
  (error) => {
    console.error("❌ RAG API Response Error:", error);

    if (error.response?.status === 401) {
      // Redirect to login or refresh token
      localStorage.removeItem("token");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

ocrAPI.interceptors.response.use(
  (response) => {
    console.log(
      `✅ OCR API Success: ${response.status} ${response.config.url}`
    );
    return response;
  },
  (error) => {
    console.error("❌ OCR API Response Error:", error);

    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// Export để các service khác sử dụng
export { ragAPI as default };
