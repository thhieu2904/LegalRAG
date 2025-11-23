/**
 * Query Service API
 */

import { apiClient } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type {
  ChatRequest,
  ChatResponse,
  SearchRequest,
  SearchResponse,
  HealthResponse,
} from '@/types';

/**
 * Send chat request to LLM
 */
export const sendChatMessage = async (request: ChatRequest): Promise<ChatResponse> => {
  const response = await apiClient.post<ChatResponse>(ENDPOINTS.QUERY.CHAT, request);
  return response.data;
};

/**
 * Search without LLM
 */
export const searchDocuments = async (request: SearchRequest): Promise<SearchResponse> => {
  const response = await apiClient.post<SearchResponse>(ENDPOINTS.QUERY.CHAT, request);
  return response.data;
};

/**
 * Check query service health
 */
export const checkQueryHealth = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>(ENDPOINTS.QUERY.HEALTH);
  return response.data;
};
