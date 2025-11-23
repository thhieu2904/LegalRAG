/**
 * Admin Service API
 * Collections & Documents CRUD operations
 */

import { apiClient } from './client';
import { ENDPOINTS } from './endpoints';
import type {
  Collection,
  CollectionResponse,
  CollectionsListResponse,
  CreateCollectionRequest,
  UpdateCollectionRequest,
  DeleteCollectionResponse,
  DocumentsListResponse,
  DocumentDetailResponse,
  UpdateDocumentRequest,
  UpdateDocumentResponse,
  DeleteDocumentResponse,
} from '@/types/admin.types';

// ============================================
// COLLECTIONS API
// ============================================

/**
 * Get all collections
 */
export async function getCollections(): Promise<Collection[]> {
  const response = await apiClient.get<CollectionsListResponse>(ENDPOINTS.ADMIN.COLLECTIONS);
  return response.data.collections;
}

/**
 * Create new collection
 */
export async function createCollection(data: CreateCollectionRequest): Promise<CollectionResponse> {
  const response = await apiClient.post<CollectionResponse>(ENDPOINTS.ADMIN.COLLECTIONS, data);
  return response.data;
}

/**
 * Update collection
 */
export async function updateCollection(
  id: string,
  data: UpdateCollectionRequest
): Promise<CollectionResponse> {
  const response = await apiClient.patch<CollectionResponse>(
    ENDPOINTS.ADMIN.COLLECTION_BY_ID(id),
    data
  );
  return response.data;
}

/**
 * Delete collection (hard delete with CASCADE)
 */
export async function deleteCollection(id: string): Promise<DeleteCollectionResponse> {
  const response = await apiClient.delete<DeleteCollectionResponse>(
    ENDPOINTS.ADMIN.COLLECTION_BY_ID(id)
  );
  return response.data;
}

// ============================================
// DOCUMENTS API
// ============================================

/**
 * Get documents list with optional filters
 */
export async function getDocuments(params?: {
  collection_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<DocumentsListResponse> {
  const response = await apiClient.get<DocumentsListResponse>(ENDPOINTS.ADMIN.DOCUMENTS, {
    params,
  });
  return response.data;
}

/**
 * Get document detail
 */
export async function getDocumentDetail(id: string): Promise<DocumentDetailResponse> {
  const response = await apiClient.get<DocumentDetailResponse>(ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id));
  return response.data;
}

/**
 * Update document title
 */
export async function updateDocument(
  id: string,
  data: UpdateDocumentRequest
): Promise<UpdateDocumentResponse> {
  const response = await apiClient.patch<UpdateDocumentResponse>(
    ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id),
    data
  );
  return response.data;
}

/**
 * Delete document (hard delete with CASCADE)
 */
export async function deleteDocument(id: string): Promise<DeleteDocumentResponse> {
  const response = await apiClient.delete<DeleteDocumentResponse>(
    ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id)
  );
  return response.data;
}

/**
 * Upload document to collection
 */
export async function uploadDocument(
  file: File,
  collection_id: string
): Promise<{ success: boolean; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('collection_id', collection_id);

  const response = await apiClient.post<{ success: boolean; message: string }>(
    '/process-document',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}

/**
 * Replace document file
 */
export async function replaceDocument(
  id: string,
  file: File,
  keep_title: boolean = true
): Promise<{ success: boolean; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('keep_title', keep_title.toString());

  const response = await apiClient.post<{ success: boolean; message: string }>(
    ENDPOINTS.ADMIN.DOCUMENT_REPLACE(id),
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  return response.data;
}
