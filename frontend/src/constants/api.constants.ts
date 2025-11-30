/**
 * API Configuration Constants
 *
 * Direct service URLs (no gateway needed):
 * - Admin Service: localhost:8001
 * - Query Service: localhost:8002
 * - Form Service: localhost:8015 (via query-service)
 * - Storage Service: localhost:8010
 */

/**
 * Service Base URLs
 * Development: Direct service ports
 * Production: Single API gateway or load balancer
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

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
