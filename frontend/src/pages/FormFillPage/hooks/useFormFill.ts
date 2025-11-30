/**
 * useFormFill Hook
 *
 * Manages all state and logic for form filling:
 * - Form loading and rendering
 * - CCCD scanning
 * - Form data management
 * - Download logic
 */

import { useState, useCallback } from 'react';
import { queryClient } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import type {
  CCCDData,
  FormRenderResponse,
  CCCDScanResponse,
  FormFillResponse,
  FormSaveResponse,
} from '../types';

// Session storage key (must match chatStore.ts)
const SESSION_ID_KEY = 'legalrag_session_id';

export const useFormFill = () => {
  // Form state
  const [formHtml, setFormHtml] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [templatePath, setTemplatePath] = useState<string>('');
  const [formId, setFormId] = useState<string>(''); // Document ID for save
  const [formName, setFormName] = useState<string>(''); // Form filename for save

  // CCCD state
  const [cccdData, setCccdData] = useState<CCCDData | null>(null);
  const [cccdScanning, setCccdScanning] = useState(false);

  // Form data (merged CCCD + manual)
  const [formData, setFormData] = useState<Record<string, string>>({});

  // Download state
  const [downloadLoading, setDownloadLoading] = useState(false);

  /**
   * Load and render form
   */
  const loadForm = useCallback(async (docId: string, formFilename: string) => {
    setFormLoading(true);
    setFormError(null);

    try {
      // Build template path: forms/{docId}/{formFilename}
      const path = `forms/${docId}/${formFilename}`;
      setTemplatePath(path);
      setFormId(docId); // Save docId for save operation
      setFormName(formFilename); // Save filename for save operation

      // Call render API
      const response = await queryClient.post<FormRenderResponse>(ENDPOINTS.QUERY.FORMS.RENDER, {
        template_path: path,
      });

      if (!response.data.success) {
        throw new Error(response.data.message);
      }

      setFormHtml(response.data.html_content || null);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Không thể tải biểu mẫu';
      setFormError(message);
      console.error('Load form error:', error);
    } finally {
      setFormLoading(false);
    }
  }, []);

  /**
   * Handle CCCD scan - Display only, no auto-fill to form
   */
  const handleCCCDScan = useCallback(async (imageData: string) => {
    setCccdScanning(true);

    try {
      // Call scan API
      const response = await queryClient.post<CCCDScanResponse>(ENDPOINTS.QUERY.FORMS.CCCD_SCAN, {
        image_data: imageData,
      });

      if (!response.data.success || !response.data.data) {
        throw new Error(response.data.message || 'Không thể quét CCCD');
      }

      // Backend returns data with scan_ prefix directly
      const cccdData = response.data.data;

      // Save CCCD data for display only - NO auto-fill to form
      setCccdData(cccdData);

      console.log('✅ CCCD scanned successfully:', cccdData);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Lỗi quét CCCD';
      alert(message);
      console.error('CCCD scan error:', error);
    } finally {
      setCccdScanning(false);
    }
  }, []);

  /**
   * Reset CCCD data
   */
  const resetCCCD = useCallback(() => {
    setCccdData(null);
    // Remove scan_ fields from form data
    setFormData((prev) => {
      const newData = { ...prev };
      Object.keys(newData).forEach((key) => {
        if (key.startsWith('scan_')) {
          delete newData[key];
        }
      });
      return newData;
    });
  }, []);

  /**
   * Handle field change (manual input)
   */
  const handleFieldChange = useCallback((fieldName: string, value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
  }, []);

  /**
   * Download filled form and save to storage
   */
  const handleDownload = useCallback(async () => {
    if (!templatePath) {
      alert('Chưa có biểu mẫu để tải');
      return;
    }

    setDownloadLoading(true);

    try {
      // Get session ID from sessionStorage
      const sessionId = sessionStorage.getItem(SESSION_ID_KEY);
      if (!sessionId) {
        console.warn('⚠️ No session ID found - form will not be saved to storage');
      }

      // Get CCCD number from scanned data or form data
      const cccdNumber = cccdData?.scan_cccd || formData['scan_cccd'] || undefined;

      // Call fill API
      const response = await queryClient.post<FormFillResponse>(ENDPOINTS.QUERY.FORMS.FILL, {
        template_path: templatePath,
        data: formData,
      });

      if (!response.data.success || !response.data.file_bytes) {
        throw new Error(response.data.message || 'Không thể tải biểu mẫu');
      }

      const fileBytes = response.data.file_bytes;
      const filename = response.data.filename || 'form.docx';

      // Save to MinIO and database if session exists
      if (sessionId && formId) {
        try {
          const saveResponse = await queryClient.post<FormSaveResponse>(
            ENDPOINTS.QUERY.FORMS.SAVE,
            {
              file_bytes: fileBytes,
              session_id: sessionId,
              form_id: formId,
              form_name: formName || filename,
              cccd_number: cccdNumber,
            }
          );

          if (saveResponse.data.success) {
            console.log('✅ Form saved to storage:', saveResponse.data.saved_path);
            console.log('✅ Submission ID:', saveResponse.data.submission_id);
          } else {
            console.warn('⚠️ Failed to save form:', saveResponse.data.message);
          }
        } catch (saveError) {
          console.error('⚠️ Error saving form to storage:', saveError);
          // Continue with download even if save fails
        }
      }

      // Convert base64 to blob for download
      const byteCharacters = atob(fileBytes);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });

      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      alert('✅ Đã tải xuống biểu mẫu thành công!');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Lỗi tải xuống';
      alert(message);
      console.error('Download error:', error);
    } finally {
      setDownloadLoading(false);
    }
  }, [templatePath, formData, formId, formName, cccdData]);

  return {
    // Form state
    formHtml,
    formLoading,
    formError,

    // CCCD state
    cccdData,
    cccdScanning,

    // Actions
    loadForm,
    handleCCCDScan,
    resetCCCD,
    handleFieldChange,
    handleDownload,
    downloadLoading,
  };
};
