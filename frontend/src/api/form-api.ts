/**
 * Form API Service - Tích hợp với RAG Service và IdentiFill Service
 * Hỗ trợ luồng: validate form → render form → auto-fill CCCD
 */

import { ragAPI, identifillAPI } from "./axios-config";
import type { CCCDData } from "./qr-scanner-api";

export interface FormRenderResult {
  html_content: string;
  raw_html: string;
  placeholders: Placeholder[];
  form_metadata: FormMetadata;
}

export interface Placeholder {
  type: "braces" | "dots" | "underscores";
  name: string;
  pattern: string;
  field_type: "text" | "date" | "email" | "number" | "select";
}

export interface FormMetadata {
  collection_id: string;
  doc_id: string;
  form_filename: string;
  conversion_messages: string[];
}

export interface AutoFillResult {
  filled_html: string;
  original_html: string;
  placeholders: Placeholder[];
  fill_preview: FillPreview;
  form_metadata: FormMetadata;
}

export interface FillPreview {
  total_placeholders: number;
  fillable_fields: FillableField[];
  unfillable_fields: UnfillableField[];
  fill_rate: number;
}

export interface FillableField {
  field_name: string;
  field_type: string;
  cccd_value: string;
  cccd_source: string;
}

export interface UnfillableField {
  field_name: string;
  field_type: string;
  reason: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

// RAG Service API Responses
export interface FormValidationResponse {
  success: boolean;
  data: {
    file_path: string;
    file_size: number;
    file_exists: boolean;
    filename: string;
  };
}

export interface FormDataResponse {
  success: boolean;
  data: {
    mapping: Record<string, unknown>;
    form_file_path: string;
    form_exists: boolean;
    collection_id: string;
    doc_id: string;
    form_filename: string;
  };
}

export const formAPI = {
  /**
   * Bước 1: Validate form tồn tại (RAG Service)
   */
  async validateForm(
    collectionId: string,
    docId: string,
    formFilename: string
  ): Promise<FormValidationResponse> {
    try {
      const response = await ragAPI.get(
        `/api/forms/file/${collectionId}/${docId}/${formFilename}`
      );
      return response.data;
    } catch (error) {
      console.error("Error validating form:", error);
      throw error;
    }
  },

  /**
   * Bước 2: Lấy form data và mapping (RAG Service)
   */
  async getFormData(
    collectionId: string,
    docId: string,
    formFilename: string
  ): Promise<FormDataResponse> {
    try {
      const response = await ragAPI.get(
        `/api/forms/data/${collectionId}/${docId}/${formFilename}`
      );
      return response.data;
    } catch (error) {
      console.error("Error getting form data:", error);
      throw error;
    }
  },
  /**
   * Bước 3: Render DOCX thành HTML (IdentiFill Service)
   */
  async renderForm(
    collectionId: string,
    docId: string,
    formFilename: string
  ): Promise<FormRenderResult> {
    try {
      const response = await identifillAPI.get<ApiResponse<FormRenderResult>>(
        `/api/v1/forms/render/${collectionId}/${docId}/${formFilename}`
      );

      if (!response.data.success) {
        throw new Error(response.data.message);
      }

      return response.data.data;
    } catch (error) {
      console.error("Error rendering form:", error);
      throw error;
    }
  },

  /**
   * Luồng tích hợp: Validate → Get Data → Render
   */
  async loadFormComplete(
    collectionId: string,
    docId: string,
    formFilename: string
  ) {
    try {
      console.log(`🔍 Loading form: ${collectionId}/${docId}/${formFilename}`);

      // Step 1: Validate form exists
      const validation = await this.validateForm(
        collectionId,
        docId,
        formFilename
      );
      if (!validation.success || !validation.data.file_exists) {
        throw new Error(`Form not found: ${formFilename}`);
      }

      // Step 2: Skip mapping data for now - render form directly
      const renderResult = await this.renderForm(
        collectionId,
        docId,
        formFilename
      );

      console.log("✅ Form loaded successfully");

      return {
        validation: validation.data,
        formData: null, // Skip mapping data
        rendered: renderResult,
        success: true,
      };
    } catch (error) {
      console.error("❌ Error loading form:", error);
      throw error;
    }
  },

  /**
   * Auto-fill form với CCCD data
   */
  async autoFillForm(
    collectionId: string,
    docId: string,
    formFilename: string,
    cccdData: CCCDData
  ): Promise<AutoFillResult> {
    try {
      const response = await identifillAPI.post<ApiResponse<AutoFillResult>>(
        `/forms/auto-fill/${collectionId}/${docId}/${formFilename}`,
        cccdData
      );

      if (!response.data.success) {
        throw new Error(response.data.message);
      }

      return response.data.data;
    } catch (error) {
      console.error("Error auto-filling form:", error);
      throw error;
    }
  },

  /**
   * Preview auto-fill process
   */
  async previewAutoFill(
    collectionId: string,
    docId: string,
    formFilename: string,
    cccdData: CCCDData
  ): Promise<FillPreview> {
    try {
      const response = await identifillAPI.get<ApiResponse<FillPreview>>(
        `/forms/preview-fill/${collectionId}/${docId}/${formFilename}`,
        {
          params: { cccd_data: JSON.stringify(cccdData) },
        }
      );

      if (!response.data.success) {
        throw new Error(response.data.message);
      }

      return response.data.data;
    } catch (error) {
      console.error("Error getting fill preview:", error);
      throw error;
    }
  },
};
