/**
 * API Configuration Constants
 *
 * All requests go through Kong Gateway (localhost:8000)
 * Kong routes requests to appropriate backend services:
 * - /query/* → query-service (8006)
 * - /admin/* → admin-service (8007)
 */

/**
 * Kong Gateway Base URL
 * Development: http://localhost:8000 (Kong proxy port)
 * Production: https://api.yourdomain.com
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * API Timeout
 * Longer timeout for document upload/processing and LLM operations
 */
export const API_TIMEOUT = 300000; // 300 seconds (5 minutes for document processing)

/**
 * API Headers
 */
export const API_HEADERS = {
  'Content-Type': 'application/json',
} as const;
