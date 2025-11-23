/**
 * 📄 Document Preview API
 * Handles document content preview (DOCX and JSON)
 *
 * Architecture:
 * - Admin Service fetches from RAG Service (API Gateway pattern)
 * - DOCX: RAG serves raw file → Admin renders to HTML with mammoth
 * - JSON: RAG serves processed JSON → Admin returns directly
 */

import { adminAPI } from "./axios-config";

/**
 * Response interface for document preview
 */
export interface DocumentPreviewResponse {
  success: boolean;
  doc_id: string;
  collection: string;
  type: "docx" | "json";
  filename?: string;
  rendered_by?: string;
  // For DOCX preview
  html?: string;
  messages?: string[];
  // For JSON preview
  data?: Record<string, unknown>;
  // Error handling
  error?: string;
}

/**
 * Get DOCX document preview as HTML
 */
export const getDocxPreview = async (
  collectionName: string,
  docId: string
): Promise<DocumentPreviewResponse> => {
  try {
    const response = await adminAPI.get(
      `/api/collections/${collectionName}/documents/${docId}/preview/docx`
    );
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching DOCX preview:", error);
    throw error;
  }
};

/**
 * Get JSON document data
 */
export const getJsonPreview = async (
  collectionName: string,
  docId: string
): Promise<DocumentPreviewResponse> => {
  try {
    const response = await adminAPI.get(
      `/api/collections/${collectionName}/documents/${docId}/preview/json`
    );
    return response.data;
  } catch (error) {
    console.error("❌ Error fetching JSON preview:", error);
    throw error;
  }
};

/**
 * Generic preview function
 */
export const getDocumentPreview = async (
  collectionName: string,
  docId: string,
  type: "docx" | "json"
): Promise<DocumentPreviewResponse> => {
  if (type === "docx") {
    return getDocxPreview(collectionName, docId);
  } else {
    return getJsonPreview(collectionName, docId);
  }
};
