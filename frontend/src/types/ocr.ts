export interface CCCDExtractedData {
  id_number?: string;
  full_name?: string;
  date_of_birth?: string;
  gender?: string;
  nationality?: string;
  hometown?: string;
  residence?: string;
  issue_date?: string;
  expiry_date?: string;
  issued_by?: string;
}

export interface ConfidenceScores {
  id_number?: number;
  full_name?: number;
  date_of_birth?: number;
  gender?: number;
  nationality?: number;
  hometown?: number;
  residence?: number;
  issue_date?: number;
  expiry_date?: number;
  overall_confidence?: number;
}

export type ProcessingStatus =
  | "pending"
  | "processing"
  | "completed"
  | "failed"
  | "expired";

export type CCCDSide = "front" | "back";

export interface CCCDSession {
  session_id: string;
  front_image_key?: string;
  back_image_key?: string;
  extracted_data?: CCCDExtractedData;
  confidence_scores?: ConfidenceScores;
  processing_status: ProcessingStatus;
  error_message?: string;
  created_at: string;
  updated_at: string;
  expires_at: string;
  processing_time?: number;
}

export interface ImageUploadRequest {
  session_id?: string;
  side: CCCDSide;
  image_data: string;
  image_format: string;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data?: T;
  message: string;
  session_id?: string;
  processing_time?: number;
  timestamp?: string;
}
