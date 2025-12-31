/**
 * Form Types
 * Types for legal forms associated with documents
 */

export interface Form {
  id: string;
  form_code: string | null;
  form_name: string;
  form_type: string | null;
  description: string | null;
  instructions: string | null;
  template_path: string | null;
  preview_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateFormRequest {
  document_id: string;
  form_code?: string;
  form_name: string;
  form_type?: string;
  description?: string;
  instructions?: string;
  file: File;
}

export interface ListFormsResponse {
  success: boolean;
  total: number;
  forms: Form[];
}

export interface DeleteFormResponse {
  success: boolean;
  message: string;
  form_id: string;
  file_deleted: boolean;
}
