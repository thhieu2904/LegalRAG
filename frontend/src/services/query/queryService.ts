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
} from '@/types';

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
