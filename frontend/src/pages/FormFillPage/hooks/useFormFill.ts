/**
 * useFormFill Hook
 *
 * Manages all state and logic for form filling:
 * - Form loading and rendering
 * - CCCD scanning
 * - Form data management
 * - Download logic
 */

import { useState, useCallback, useRef } from 'react';
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

  // Store response data for modal confirmation flow
  const pendingDownloadRef = useRef<{
    fileBytes: string;
    filename: string;
    totalFields: number;
    filledFields: number;
    sessionId: string | null;
    cccdNumber?: string;
  } | null>(null);

  // Modal/Toast state
  const [validationModal, setValidationModal] = useState<{
    isOpen: boolean;
    totalFields: number;
    filledFields: number;
    missingCount: number;
  }>({ isOpen: false, totalFields: 0, filledFields: 0, missingCount: 0 });

  const [toast, setToast] = useState<{
    show: boolean;
    message: string;
    variant: 'success' | 'error' | 'info';
  }>({ show: false, message: '', variant: 'success' });

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
   * Execute actual download (called after modal confirmation or directly)
   */
  const executeDownload = useCallback(async () => {
    if (!pendingDownloadRef.current) {
      console.error('No pending download data');
      return;
    }

    const { fileBytes, filename, totalFields, filledFields, sessionId, cccdNumber } =
      pendingDownloadRef.current;

    setDownloadLoading(true);

    try {
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

      // Show success toast based on validation
      if (filledFields === totalFields) {
        setToast({
          show: true,
          message: `Đã tải xuống biểu mẫu thành công! Đã điền đầy đủ tất cả ${totalFields} trường.`,
          variant: 'success',
        });
      } else {
        setToast({
          show: true,
          message: `Đã tải xuống biểu mẫu! Lưu ý: Đã điền ${filledFields}/${totalFields} trường.`,
          variant: 'info',
        });
      }

      // Clear pending download
      pendingDownloadRef.current = null;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Lỗi tải xuống';
      setToast({ show: true, message, variant: 'error' });
      console.error('Download error:', error);
    } finally {
      setDownloadLoading(false);
    }
  }, [formId, formName]);

  /**
   * Download filled form and save to storage
   */
  const handleDownload = useCallback(async () => {
    if (!templatePath) {
      setToast({ show: true, message: 'Chưa có biểu mẫu để tải', variant: 'error' });
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
      const cccdNumber = cccdData?.field_cccd || formData['field_cccd'] || undefined;

      // Call fill API
      const response = await queryClient.post<FormFillResponse>(ENDPOINTS.QUERY.FORMS.FILL, {
        template_path: templatePath,
        data: formData,
        session_id: sessionId || undefined,
        form_name: formName || undefined,
      });

      if (!response.data.success || !response.data.file_bytes) {
        throw new Error(response.data.message || 'Không thể tải biểu mẫu');
      }

      const fileBytes = response.data.file_bytes;
      const filename = response.data.filename || 'form.docx';
      const totalFields = response.data.total_fields || 0;
      const filledFields = response.data.filled_fields || 0;

      // Store response for later execution
      pendingDownloadRef.current = {
        fileBytes,
        filename,
        totalFields,
        filledFields,
        sessionId,
        cccdNumber,
      };

      // Show validation notification - use modal for confirmation
      if (filledFields < totalFields) {
        const missingCount = totalFields - filledFields;

        setValidationModal({
          isOpen: true,
          totalFields,
          filledFields,
          missingCount,
        });

        // Wait for user confirmation via modal
        setDownloadLoading(false);
        return;
      }

      // If complete, execute download immediately
      await executeDownload();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Lỗi tải xuống';
      setToast({ show: true, message, variant: 'error' });
      console.error('Download error:', error);
      setDownloadLoading(false);
    }
  }, [templatePath, formData, formName, cccdData, executeDownload]);

  return {
    // Form state
    formHtml,
    formLoading,
    formError,

    // CCCD state
    cccdData,
    cccdScanning,

    // Modal/Toast state
    validationModal,
    setValidationModal,
    toast,
    setToast,

    // Actions
    loadForm,
    handleCCCDScan,
    resetCCCD,
    handleFieldChange,
    handleDownload,
    executeDownload,
    downloadLoading,
  };
};
