/**
 * API Endpoints Configuration
 *
 * Direct service URLs (no Kong Gateway)
 * - Admin Service: localhost:8001
 * - Query Service: localhost:8002
 */

export const ENDPOINTS = {
  // Admin Service (direct: localhost:8001)
  ADMIN: {
    // Collections CRUD
    COLLECTIONS: '/admin/collections',
    COLLECTION_BY_ID: (id: string) => `/admin/collections/${id}`,

    // Documents CRUD
    DOCUMENTS: '/admin/documents',
    DOCUMENT_BY_ID: (id: string) => `/admin/documents/${id}`,
    DOCUMENT_REPLACE: (id: string) => `/admin/documents/${id}/replace`,

    // Health
    HEALTH: '/health',
  },

  // Query Service (direct: localhost:8002)
  QUERY: {
    CHAT: '/query', // Main RAG query endpoint
    CONFIRM: '/query/confirm', // Confirm document selection (after clarification)

    // Session management (backend-driven)
    SESSION_START: '/session/start', // Start new session (F5/refresh)
    SESSION_CLEAR: '/session/clear', // Clear session (unpin document)
    SESSION_INFO: '/session/info', // Get session info (append /{session_id})

    HEALTH: '/health',
  },
} as const;
