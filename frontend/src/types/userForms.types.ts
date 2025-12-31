/**
 * User Forms Types - For admin management of user-filled forms
 */

export interface UserFormItem {
  file_path: string; // Full path in MinIO
  filename: string; // Just the filename
  session_id: string; // Session ID
  cccd_number: string | null; // CCCD extracted from filename
  form_name: string; // Form name without CCCD prefix
  file_size: number | null;
  created_at: string | null;
}

export interface UserFormListResponse {
  success: boolean;
  message: string;
  forms: UserFormItem[];
  total: number;
}

export interface UserFormDeleteResponse {
  success: boolean;
  message: string;
  deleted_path: string | null;
}
