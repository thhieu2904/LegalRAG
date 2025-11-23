/**
 * Admin Types - Collections & Documents Management (LegalRAG)
 */

// ============================================
// COLLECTION TYPES
// ============================================

export interface Collection {
  id: string; // UUID
  name: string; // Slug: "ho_tich", "bo_luat_dan_su"
  display_name: string; // Display: "Hộ tịch", "Bộ luật dân sự"
  description: string | null;
  icon: string; // Icon name: "file-text", "shield-check"
  color: string; // Hex color: "#3b82f6", "#10b981"
  document_count: number;
  total_chunks: number;
  is_active: boolean;
  created_at: string; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface CreateCollectionRequest {
  name: string;
  display_name: string;
  description?: string;
  icon?: string; // Default: "file-text"
  color?: string; // Default: "#3b82f6"
}

export interface UpdateCollectionRequest {
  display_name?: string;
  description?: string;
  icon?: string;
  color?: string;
  is_active?: boolean;
}

export interface CollectionResponse {
  success: boolean;
  collection: Collection;
  message?: string;
}

export interface CollectionsListResponse {
  success: boolean;
  collections: Collection[];
}

export interface DeleteCollectionResponse {
  success: boolean;
  message: string;
  collection_id: string;
  deleted_documents: number;
  deleted_chunks_estimate: number;
}

// ============================================
// DOCUMENT TYPES
// ============================================

export interface Document {
  id: string; // UUID
  collection_id: string; // UUID foreign key
  title: string;
  filename: string;
  file_path: string | null;
  file_size: number | null; // bytes
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  metadata: Record<string, any> | null; // JSONB extracted metadata
  created_at: string; // ISO datetime
  processed_at: string | null; // ISO datetime
  updated_at: string; // ISO datetime
}

export interface DocumentsListResponse {
  success: boolean;
  total: number;
  limit: number;
  offset: number;
  documents: Document[];
}

export interface DocumentDetailResponse {
  success: boolean;
  document: Document & {
    actual_chunks: number; // Real-time chunk count
  };
}

export interface UpdateDocumentRequest {
  title: string;
}

export interface UpdateDocumentResponse {
  success: boolean;
  message: string;
  document: {
    id: string;
    title: string;
    updated_at: string;
  };
}

export interface DeleteDocumentResponse {
  success: boolean;
  message: string;
  document_id: string;
  deleted_chunks: number;
  file_deleted: boolean;
  file_path: string | null;
}

export interface ReplaceDocumentResponse {
  success: boolean;
  message: string;
  document: Document;
  old_chunks_deleted: number;
  new_chunks_created: number;
  processing_time: number; // seconds
}

export interface UploadDocumentResponse {
  success: boolean;
  message: string;
  document: Document;
  chunks_created: number;
  processing_time: number; // seconds
}

// ============================================
// STATS & HEALTH
// ============================================

/**
 * Stats
 */
export interface Stats {
  total_documents: number;
  total_vectors: number;
  total_chunks: number;
  total_khoa: number;
}

/**
 * Health Response
 */
export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  service: string;
  [key: string]: boolean | string;
}

/**
 * Chuyên Ngành (Major/Program) - for dropdown
 */
export interface ChuyenNganh {
  ma_chuyen_nganh: string;
  ten_chuyen_nganh: string;
  is_active: boolean;
}

/**
 * Môn Học (Course/Subject) - for dropdown
 */
export interface MonHoc {
  ma_mon: string;
  ten_mon: string;
  ma_chuyen_nganh: string;
  so_tin_chi: number | null;
  is_active: boolean;
}

/**
 * Loại Tài Liệu (Document Type) - for dropdown
 */
export interface LoaiTaiLieu {
  ma_loai: string;
  ten_loai: string;
  mo_ta?: string;
  thu_tu_hien_thi: number;
  is_active: boolean;
}
