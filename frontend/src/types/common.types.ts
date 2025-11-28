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
 * Source (matching Query Service API response)
 * Represents a legal document source used in the answer
 */
export interface Source {
  content: string;
  similarity: number;
  document_title?: string; // Tên văn bản pháp luật (VD: "Luật Hôn nhân 2014")
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
