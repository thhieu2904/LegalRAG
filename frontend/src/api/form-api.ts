/**
 * Form API Service - Integration với IdentiFill Service
 * Xử lý form rendering và auto-fill logic
 */

import { identifillAPI } from "./axios-config";
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

export const formAPI = {
  /**
   * Render DOCX form thành HTML
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
