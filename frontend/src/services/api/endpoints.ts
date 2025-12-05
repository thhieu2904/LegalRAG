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

    // Forms management
    FORMS: '/admin/forms',
    // List forms for a specific document
    FORMS_BY_DOCUMENT: (id: string) => `/admin/documents/${id}/forms`,
    FORM_BY_ID: (id: string) => `/admin/forms/${id}`,
    FORM_TEMPLATES: '/admin/form-templates',

    // Hybrid form template creation (detect + finalize)
    PROCESS_TEMPLATE_DETECT: '/admin/forms/process-template/detect',
    PROCESS_TEMPLATE_FINALIZE: '/admin/forms/process-template/finalize',
    PROCESS_TEMPLATE_PREVIEW: '/admin/templates/preview',

    // User-filled forms management
    USER_FORMS: '/admin/user-forms',
    USER_FORMS_BY_SESSION: (sessionId: string) => `/admin/user-forms/${sessionId}`,
    DELETE_USER_FORM: (sessionId: string, formName: string) =>
      `/admin/user-forms/${sessionId}/${formName}`,

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

    // Form operations (via form-service:8015)
    FORMS: {
      HEALTH: '/forms/health',
      CCCD_SCAN: '/forms/cccd/scan', // POST with base64 image
      RENDER: '/forms/render', // POST with form_path
      FILL: '/forms/fill', // POST with form_path and data
      SAVE: '/forms/save', // POST to save filled form to storage
    },

    HEALTH: '/health',
  },
} as const;
