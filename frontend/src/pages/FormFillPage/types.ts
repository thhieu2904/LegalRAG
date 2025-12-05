/**
 * API Types for FormFillPage
 */

// CCCD Data from backend - unified field naming
export interface CCCDData {
  field_cccd: string; // Số căn cước công dân
  field_cmnd?: string; // Số CMND cũ (optional)
  field_ho_ten: string; // Họ và tên
  field_ngay_sinh: string; // Ngày sinh
  field_gioi_tinh: string; // Giới tính
  field_dia_chi: string; // Địa chỉ
  field_ngay_cap: string; // Ngày cấp
}

// Form render response
export interface FormRenderResponse {
  success: boolean;
  message: string;
  html_content?: string; // Match backend field name
  raw_html?: string;
  placeholders?: string[];
  template_path?: string;
}

// Form fill response
export interface FormFillResponse {
  success: boolean;
  message: string;
  file_bytes?: string; // base64 encoded DOCX
  saved_path?: string;
  filename?: string;
}

// Form save request
export interface FormSaveRequest {
  file_bytes: string; // base64 encoded DOCX
  session_id: string;
  form_id: string; // Document ID (docId from URL)
  form_name: string;
  cccd_number?: string;
}

// Form save response
export interface FormSaveResponse {
  success: boolean;
  message: string;
  saved_path?: string;
  submission_id?: string;
}

// CCCD scan response
export interface CCCDScanResponse {
  success: boolean;
  message?: string;
  data?: CCCDData;
  processing_time?: number;
  confidence?: number;
}
