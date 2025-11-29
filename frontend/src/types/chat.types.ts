/**
 * Chat Related Types
 */

import type { MessageRole, Source, FormInfo } from './common.types';

/**
 * Document Option (for clarification)
 */
export interface DocumentOption {
  document_id: string;
  title: string;
  chunk_count: number;
  confidence: number;
  preview: string;
}

/**
 * Session Info (from backend)
 */
export interface SessionInfo {
  session_id: string;
  is_new_session: boolean;
  pinned_document_id?: string | null;
  pinned_document_title?: string | null;
  conversation_turns: number;
}

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
  forms?: FormInfo[]; // Forms attached to source documents
  timestamp: Date;
  tokens?: number;
  took_ms?: number;
  confidence?: number;
  query?: string; // Original user question (for keyword highlighting in sources)

  // Clarification fields
  needs_clarification?: boolean;
  document_options?: DocumentOption[];
  originalQuestion?: string; // Store original question for confirm request
}

/**
 * History Message (for API requests)
 */
export interface HistoryMessage {
  role: 'user' | 'assistant';
  content: string;
}

/**
 * Chat Request (matching Query Service API)
 */
export interface ChatRequest {
  question: string;
  session_id?: string | null; // null = request new session from backend
  top_k?: number;
  threshold?: number;
  history?: HistoryMessage[]; // Last 3 turns for follow-up context
}

/**
 * Confirm Document Request (when user selects a document option)
 */
export interface ConfirmRequest {
  question: string;
  document_id: string;
  session_id?: string | null; // For conversation state tracking
  history?: HistoryMessage[]; // Chat history for follow-up context
}

/**
 * Chat Response (matching Query Service API)
 */
export interface ChatResponse {
  success: boolean;
  question: string;
  answer: string | null;
  sources: Source[];
  forms?: FormInfo[]; // Forms attached to source documents
  tokens_used: number;

  // Session info (always included)
  session_id: string;
  session_info?: SessionInfo;

  // Clarification fields
  needs_clarification?: boolean;
  clarification_message?: string;
  document_options?: DocumentOption[];

  // Conversation state info (for debugging/transparency)
  used_pinned_document?: boolean;
  pinned_document_title?: string;
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
