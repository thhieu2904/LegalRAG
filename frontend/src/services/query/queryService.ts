/**
 * Query Service API
 */

import { queryClient } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type {
  ChatRequest,
  ChatResponse,
  ConfirmRequest,
  SearchRequest,
  SearchResponse,
  HealthResponse,
  SessionInfo,
} from '@/types';

// ============= SESSION API =============

/**
 * Session start request/response types
 */
interface SessionStartResponse {
  success: boolean;
  session_info: SessionInfo;
  message: string;
}

interface ClearSessionRequest {
  session_id: string;
}

interface ClearSessionResponse {
  success: boolean;
  session_id: string;
  message: string;
}

interface SessionInfoResponse {
  success: boolean;
  session_info?: SessionInfo;
  message: string;
}

/**
 * Start a new session (called on F5/refresh/new tab)
 */
export const startSession = async (): Promise<SessionStartResponse> => {
  const response = await queryClient.post<SessionStartResponse>(ENDPOINTS.QUERY.SESSION_START);
  return response.data;
};

/**
 * Clear session (unpin document)
 */
export const clearSession = async (request: ClearSessionRequest): Promise<ClearSessionResponse> => {
  const response = await queryClient.post<ClearSessionResponse>(
    ENDPOINTS.QUERY.SESSION_CLEAR,
    request
  );
  return response.data;
};

/**
 * Get session info
 */
export const getSessionInfo = async (sessionId: string): Promise<SessionInfoResponse> => {
  const response = await queryClient.get<SessionInfoResponse>(
    `${ENDPOINTS.QUERY.SESSION_INFO}/${sessionId}`
  );
  return response.data;
};

// ============= QUERY API =============

/**
 * Send chat request to LLM
 * May return needs_clarification=true with document_options
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await queryClient.post<ChatResponse>(ENDPOINTS.QUERY.CHAT, request);
  return response.data;
};

/**
 * Confirm document selection after clarification
 * Called when user clicks on a document option button
 */
export const confirmDocument = async (request: ConfirmRequest): Promise<ChatResponse> => {
  const response = await queryClient.post<ChatResponse>(ENDPOINTS.QUERY.CONFIRM, request);
  return response.data;
};

/**
 * Search without LLM
 */
export const searchDocuments = async (request: SearchRequest): Promise<SearchResponse> => {
  const response = await queryClient.post<SearchResponse>(ENDPOINTS.QUERY.CHAT, request);
  return response.data;
};

/**
 * Check query service health
 */
export const checkQueryHealth = async (): Promise<HealthResponse> => {
  const response = await queryClient.get<HealthResponse>(ENDPOINTS.QUERY.HEALTH);
  return response.data;
};
