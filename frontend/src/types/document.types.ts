export interface Document {
  id: string;
  collection_id: string;
  title: string;
  filename: string;
  file_path: string | null;
  file_size: number | null;
  chunk_count: number;
  forms_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithForms extends Document {
  form_count?: number;
  collection_name?: string;
}

export interface CreateDocumentRequest {
  collection_id: string;
  title: string;
  file: File;
}

export interface UpdateDocumentRequest {
  title: string;
}

export interface DocumentDetailResponse {
  document: Document;
  collection_name: string;
  chunks: Array<{
    id: string;
    chunk_index: number;
    content: string;
    section_title: string | null;
  }>;
  forms: Array<{
    id: string;
    form_name: string;
    form_type: string | null;
    form_code: string | null;
    template_path: string | null;
  }>;
}

export interface ListDocumentsResponse {
  success: boolean;
  total: number;
  limit: number;
  offset: number;
  documents: Document[];
}
