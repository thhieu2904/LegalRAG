/**
 * JSON Documents API - Admin Service
 * ===================================
 *
 * API wrapper for JSON document management (CRUD operations).
 * Endpoints: Admin Service (Port 8001)
 *
 * NOTE: Uses adminAPI from axios-config.ts for centralized configuration
 */

import { adminAPI } from "./axios-config";

// Type definitions
export interface UpdateJsonDocumentRequest {
  data: Record<string, unknown>;
  trigger_rebuild?: boolean;
}

export interface UpdateJsonDocumentResponse {
  success: boolean;
  message: string;
  backup_created?: boolean;
  rebuild_triggered?: boolean;
  rebuild_task_id?: string;
  collection?: string;
  doc_id?: string;
  updated_at?: string;
  processing_time?: number;
}

/**
 * Update JSON document content
 * PUT /api/collections/{collection}/documents/{doc_id}/json
 */
export const updateJsonDocument = async (
  collection: string,
  docId: string,
  jsonData: Record<string, unknown>,
  triggerRebuild: boolean = false
): Promise<UpdateJsonDocumentResponse> => {
  const response = await adminAPI.put(
    `/api/collections/${collection}/documents/${docId}/json`,
    {
      data: jsonData,
      trigger_rebuild: triggerRebuild,
    }
  );
  return response.data;
};

/**
 * Get JSON document content
 * GET /api/collections/{collection}/documents/{doc_id}/json
 */
export const getJsonDocument = async (
  collection: string,
  docId: string
): Promise<Record<string, unknown>> => {
  const response = await adminAPI.get(
    `/api/collections/${collection}/documents/${docId}/json`
  );
  return response.data;
};
