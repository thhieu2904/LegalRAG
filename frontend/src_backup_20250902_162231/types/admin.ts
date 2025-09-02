// ============================================================================
// Core Base Models
// ============================================================================

export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
  updatedBy?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  meta?: PaginationMeta;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

// ============================================================================
// Database Management Models
// ============================================================================

export interface ProcessingStep {
  id: string;
  name: string;
  status: "pending" | "processing" | "completed" | "error";
  progress: number;
  startTime?: string;
  endTime?: string;
  errorMessage?: string;
  metadata?: Record<string, any>;
}

export interface FileInfo {
  id: string;
  filename: string;
  originalName: string;
  path: string;
  size: number;
  mimeType: string;
  checksum?: string;
  uploadedAt: string;
  status: "uploading" | "uploaded" | "processing" | "processed" | "error";
}

export interface LegalCollection extends BaseEntity {
  name: string; // URL-safe identifier
  displayName: string;
  description: string;
  category: "procedure" | "law" | "regulation" | "guidance" | "form" | "other";
  status: "active" | "inactive" | "archived";
  documentCount: number;
  totalSize: number;
  lastSyncAt?: string;
  metadata?: {
    tags?: string[];
    department?: string;
    effectiveDate?: string;
    expiredDate?: string;
  };
}

export interface LegalDocument extends BaseEntity {
  collectionId: string;
  name: string;
  fileName: string;
  version: string;
  status:
    | "draft"
    | "processing"
    | "processed"
    | "published"
    | "archived"
    | "error";

  // File references
  sourceFile: FileInfo; // Original DOC/PDF file
  processedFile?: FileInfo; // Generated JSON file
  formFile?: FileInfo; // Optional form/template file

  // Content metadata
  title: string;
  summary?: string;
  tags: string[];
  language: "vi" | "en";
  documentType: "law" | "regulation" | "procedure" | "form" | "guide" | "other";

  // Legal metadata
  documentNumber?: string;
  issuedBy?: string;
  issuedDate?: string;
  effectiveDate?: string;
  expiredDate?: string;

  // Processing info
  processingSteps?: ProcessingStep[];
  lastProcessedAt?: string;

  // Vector indexing
  isIndexed: boolean;
  indexedAt?: string;
  embeddingCount?: number;

  // Usage statistics
  viewCount?: number;
  downloadCount?: number;
  queryCount?: number;
}

export interface DocumentUploadRequest {
  collectionId: string;
  name: string;
  title: string;
  version?: string;
  tags: string[];
  documentType: LegalDocument["documentType"];
  documentNumber?: string;
  issuedBy?: string;
  issuedDate?: string;
  effectiveDate?: string;

  // Processing options
  autoProcess: boolean;
  autoIndex: boolean;
  notifyOnComplete: boolean;
}

// ============================================================================
// Vector Database Models
// ============================================================================

export interface VectorCollection extends BaseEntity {
  name: string;
  displayName: string;
  description: string;
  dimension: number;
  metricType: "cosine" | "euclidean" | "dot_product";
  status: "active" | "building" | "updating" | "error" | "maintenance";

  // Statistics
  documentCount: number;
  embeddingCount: number;
  totalSize: number;

  // Configuration
  chunkSize: number;
  chunkOverlap: number;
  embeddingModel: string;

  // Sync info
  lastSyncAt?: string;
  syncStatus?: "synced" | "out_of_sync" | "syncing";
}

export interface VectorEmbedding extends BaseEntity {
  collectionId: string;
  documentId: string;
  chunkId: string;
  content: string;
  metadata: {
    documentName: string;
    chunkIndex: number;
    pageNumber?: number;
    section?: string;
    [key: string]: any;
  };
  embedding?: number[];
  status: "pending" | "embedded" | "indexed" | "error";
}

// ============================================================================
// Question Management Models
// ============================================================================

export interface QuestionCategory extends BaseEntity {
  name: string;
  displayName: string;
  description: string;
  parentId?: string;
  level: number;
  sortOrder: number;
  isActive: boolean;
  questionCount: number;
}

export interface QuestionTemplate extends BaseEntity {
  categoryId: string;
  question: string;
  suggestedAnswer?: string;
  tags: string[];
  difficulty: "easy" | "medium" | "hard";
  isActive: boolean;
  usageCount: number;
}

export interface UserQuestion extends BaseEntity {
  sessionId: string;
  userId?: string;
  question: string;
  processedQuestion?: string;
  answer?: string;
  sources?: string[];
  confidence?: number;
  responseTime: number;
  status: "pending" | "answered" | "failed" | "flagged";
  feedback?: {
    rating: 1 | 2 | 3 | 4 | 5;
    comment?: string;
    isHelpful: boolean;
  };
  metadata?: {
    userAgent?: string;
    ipAddress?: string;
    location?: string;
  };
}

// ============================================================================
// Voice & System Models
// ============================================================================

export interface VoiceConfig extends BaseEntity {
  name: string;
  displayName: string;
  isDefault: boolean;
  isActive: boolean;

  // TTS Settings
  rate: number; // 0.5 - 2.0
  pitch: number; // 0.5 - 2.0
  volume: number; // 0.0 - 1.0
  voice: string;
  language: string;

  // Advanced settings
  pauseDuration: number;
  emphasizeKeywords: boolean;
  customPronunciation?: Record<string, string>;
}

export interface SystemConfig extends BaseEntity {
  key: string;
  value: any;
  type: "string" | "number" | "boolean" | "json" | "array";
  category: "general" | "ai" | "voice" | "security" | "storage" | "other";
  description?: string;
  isPublic: boolean;
  validation?: {
    required: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    enum?: any[];
  };
}

export interface ModelConfig extends BaseEntity {
  name: string;
  displayName: string;
  type: "llm" | "embedding" | "reranker" | "voice" | "other";
  provider: "openai" | "huggingface" | "local" | "other";
  modelId: string;
  version?: string;
  isActive: boolean;
  isDefault: boolean;

  // Configuration
  config: {
    apiKey?: string;
    endpoint?: string;
    maxTokens?: number;
    temperature?: number;
    topP?: number;
    [key: string]: any;
  };

  // Performance metrics
  averageResponseTime?: number;
  successRate?: number;
  lastUsedAt?: string;
  usageCount?: number;
}

// ============================================================================
// Modal State Management Models
// ============================================================================

export type ModalType =
  | "add-collection"
  | "edit-collection"
  | "delete-collection"
  | "add-document"
  | "edit-document"
  | "view-document"
  | "delete-document"
  | "add-question"
  | "edit-question"
  | "view-question"
  | "delete-question"
  | "upload-files"
  | "processing-details"
  | "vector-rebuild"
  | "system-config"
  | "model-config"
  | "export-data"
  | "import-data";

export interface ModalState {
  type: ModalType | null;
  isOpen: boolean;
  data?: any;
  options?: {
    size?: "sm" | "md" | "lg" | "xl" | "full";
    closable?: boolean;
    backdrop?: boolean;
  };
}

export interface ModalProps<T = any> {
  isOpen: boolean;
  onClose: () => void;
  onConfirm?: (data: T) => void | Promise<void>;
  data?: T;
  title?: string;
  size?: "sm" | "md" | "lg" | "xl" | "full";
}

// ============================================================================
// Form Models
// ============================================================================

export interface FormValidation {
  field: string;
  message: string;
  type: "required" | "format" | "min" | "max" | "custom";
}

export interface FormState<T = any> {
  data: T;
  errors: FormValidation[];
  isSubmitting: boolean;
  isDirty: boolean;
  isValid: boolean;
}

// ============================================================================
// Filter & Search Models
// ============================================================================

export interface FilterOption {
  key: string;
  label: string;
  value: any;
  count?: number;
}

export interface SearchFilter {
  field: string;
  operator:
    | "eq"
    | "ne"
    | "contains"
    | "startsWith"
    | "endsWith"
    | "in"
    | "between";
  value: any;
}

export interface SortOption {
  field: string;
  direction: "asc" | "desc";
  label?: string;
}

export interface SearchQuery {
  query?: string;
  filters: SearchFilter[];
  sort: SortOption[];
  page: number;
  limit: number;
}

// ============================================================================
// Export/Import Models
// ============================================================================

export interface ExportRequest {
  type: "collections" | "documents" | "questions" | "configs" | "all";
  format: "json" | "csv" | "xlsx";
  filters?: SearchFilter[];
  includeFiles?: boolean;
}

export interface ImportRequest {
  type: "collections" | "documents" | "questions" | "configs";
  format: "json" | "csv" | "xlsx";
  file: File;
  options?: {
    overwrite?: boolean;
    validateOnly?: boolean;
    skipErrors?: boolean;
  };
}

export interface BatchOperation {
  id: string;
  type: "import" | "export" | "process" | "index" | "delete";
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  progress: number;
  totalItems: number;
  processedItems: number;
  failedItems: number;
  startTime: string;
  endTime?: string;
  errorMessage?: string;
  results?: {
    success: any[];
    errors: any[];
  };
}
