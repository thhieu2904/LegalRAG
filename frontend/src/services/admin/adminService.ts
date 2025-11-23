/**
 * Admin Service API
 */

import { apiClient } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type { UploadRequest, ProcessDocumentResponse, HealthResponse } from '@/types';

/**
 * Process and upload document with progress tracking
 *
 * @param request - Upload request with file and metadata
 * @param onProgress - Optional callback for upload progress (0-100)
 */
export const processDocument = async (
  request: UploadRequest,
  onProgress?: (percentage: number) => void
): Promise<ProcessDocumentResponse> => {
  // Create FormData with correct field names for backend
  const formData = new FormData();
  formData.append('file', request.file);
  formData.append('ma_chuyen_nganh', request.ma_chuyen_nganh);
  formData.append('ma_mon', request.ma_mon);
  formData.append('ma_giao_vien', request.ma_giao_vien);
  formData.append('upload_type', request.upload_type);

  // Optional fields
  if (request.nam_hoc !== undefined) {
    formData.append('nam_hoc', request.nam_hoc.toString());
  }
  if (request.so_chuong !== undefined) {
    formData.append('so_chuong', request.so_chuong.toString());
  }
  if (request.force_overwrite) {
    formData.append('force_overwrite', 'true');
  }

  // DEBUG: Log FormData entries
  console.log('📋 FormData entries:');
  for (const [key, value] of formData.entries()) {
    if (key !== 'file') {
      console.log(`  ${key}:`, value);
    }
  }

  const response = await apiClient.post<ProcessDocumentResponse>(
    ENDPOINTS.ADMIN.PROCESS_DOCUMENT,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percentage);
        }
      },
    }
  );

  return response.data;
};

/**
 * Check admin service health
 */
export const checkAdminHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>(ENDPOINTS.ADMIN.HEALTH);
  return response.data;
};
