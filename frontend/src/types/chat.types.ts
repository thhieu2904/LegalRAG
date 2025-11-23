/**
 * Chat Related Types
 */

import type { MessageRole, Source } from './common.types';

/**
 * Chat Message (for conversation history)
 */
export interface Message {
  role: MessageRole;
  content: string;
}

/**
 * Chat Message (for display in UI)
 */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  timestamp: Date;
  tokens?: number;
  took_ms?: number;
  confidence?: number;
  query?: string; // Original user question (for keyword highlighting in sources)
}

/**
 * Chat Request
 */
export interface ChatRequest {
  question: string;
  history?: Message[];
  top_k?: number;
  filters?: {
    ma_khoa?: string;
    ma_mon_hoc?: string;
    nam_hoc_cap_do?: number;
    hoc_ky?: number;
    loai_noi_dung?: string;
    so_chuong?: number;
  };
  threshold?: number;
}

/**
 * Chat Response
 */
export interface ChatResponse {
  question: string;
  answer: string;
  sources: Source[];
  confidence: number;
  tokens_used: number;
  prompt_tokens: number;
  completion_tokens: number;
  finish_reason: string;
  citations: string[];
  validation_score: number;
  citation_coverage: number;
  citation_confidence: number;
  safety_ratings: Record<string, unknown>;
  took_ms: number;
}

/**
 * Search Request (without LLM)
 */
export interface SearchRequest {
  question: string;
  top_k?: number;
  filters?: Record<string, string | number | undefined>;
  threshold?: number;
}

/**
 * Search Response
 */
export interface SearchResponse {
  question: string;
  sources: Source[];
  took_ms: number;
}

/**
 * Chat Filters
 */
export interface ChatFilters {
  ma_khoa?: string;
  ma_mon_hoc?: string;
  nam_hoc_cap_do?: number;
  hoc_ky?: number;
  loai_noi_dung?: string;
  so_chuong?: number;
}
