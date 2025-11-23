/**
 * Common TypeScript Types
 */

/**
 * Generic API Response
 */
export interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  message?: string;
  status: number;
}

/**
 * Filter Options
 */
export interface FilterOptions {
  ma_khoa?: string;
  ma_mon_hoc?: string;
  nam_hoc_cap_do?: number;
  hoc_ky?: number;
  loai_noi_dung?: string;
  so_chuong?: number;
}

/**
 * Chunk Info (individual piece of document)
 */
export interface ChunkInfo {
  chunk_id: string;
  text_content: string;
  chunk_index: number;
  similarity: number;
  chunk_metadata: Record<string, unknown> | null;

  // Vector embeddings for comparison visualization
  query_embedding?: number[]; // Query vector (3072-D)
  chunk_embedding?: number[]; // Chunk vector (3072-D)
}

/**
 * Source (matching Query Service API response)
 */
export interface Source {
  content: string;
  similarity: number;
}

/**
 * Document Source (grouped chunks) - for future use
 */
export interface DocumentSource {
  document_id: string;
  file_name: string;
  upload_type: string;
  ma_chuyen_nganh: string;
  ma_mon: string;
  nam_hoc: number | null;
  chunk_count: number;
  max_similarity: number;
  chunks: ChunkInfo[];
}

/**
 * Metadata
 */
export interface Metadata {
  ma_khoa: string;
  ma_mon_hoc: string;
  so_chuong?: number | null;
  nam_hoc_cap_do?: number | null;
  hoc_ky?: number | null;
  ten_phan?: string;
  loai_noi_dung?: string;
}

/**
 * Option for Select Component
 */
export interface SelectOption<T = string | number> {
  value: T;
  label: string;
  disabled?: boolean;
}

/**
 * Pagination
 */
export interface Pagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

/**
 * Loading State
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Response Status
 */
export type ResponseStatus = 'success' | 'error' | 'loading';

/**
 * Message Role
 */
export type MessageRole = 'user' | 'assistant';
