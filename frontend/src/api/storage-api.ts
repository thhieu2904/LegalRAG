/**
 * Storage API Service
 * Communicates with backend storage endpoints for form management
 */

import axios from "axios";

const STORAGE_BASE_URL =
  import.meta.env.VITE_STORAGE_API_URL ||
  "http://localhost:8002/api/v1/storage";

export const storageAPI = axios.create({
  baseURL: STORAGE_BASE_URL,
});

// Interceptor for request logging
storageAPI.interceptors.request.use(
  (config) => {
    console.log(
      `📤 Storage API Request: ${config.method?.toUpperCase()} ${config.url}`
    );
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor for response logging
storageAPI.interceptors.response.use(
  (response) => {
    console.log(`✅ Storage API Response: ${response.status}`);
    return response;
  },
  (error) => {
    console.error(
      `❌ Storage API Error: ${error.response?.status} - ${
        error.response?.data?.detail || error.message
      }`
    );
    return Promise.reject(error);
  }
);

/**
 * Save form to storage with auto-save on download
 */
export async function saveFormToStorage(
  formFile: Blob,
  cccd: string,
  userName: string,
  formName: string,
  fileName: string
) {
  const formData = new FormData();
  formData.append("form_file", formFile, fileName);
  formData.append("scan_cccd", cccd);
  formData.append("scan_ho_ten", userName);
  formData.append("form_name", formName);

  return storageAPI.post("/save", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
}

/**
 * List all saved forms for a specific CCCD
 */
export async function listSavedForms(cccd: string) {
  return storageAPI.get(`/list/${cccd}`);
}

/**
 * Download a previously saved form from storage
 */
export async function downloadSavedForm(cccd: string, fileName: string) {
  return storageAPI.get(`/download/${cccd}/${fileName}`, {
    responseType: "blob",
  });
}

/**
 * Delete a saved form from storage
 */
export async function deleteSavedForm(
  cccd: string,
  fileId: string,
  fileName: string
) {
  return storageAPI.delete(`/delete/${cccd}/${fileId}/${fileName}`);
}

/**
 * Get storage statistics
 */
export async function getStorageStats() {
  return storageAPI.get("/stats");
}

/**
 * Check health status of storage service
 */
export async function checkStorageHealth() {
  return storageAPI.get("/health");
}
