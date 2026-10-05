import { useState, useCallback, useRef, useReducer, useEffect } from 'react';
import { queryClient } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import type { FormRenderResponse, CCCDScanResponse, FormFillResponse } from '../types';
import { createFormDraft, draftReducer } from '../draft';
import type { DraftAction } from '../draft';
import { findTemplateConfig } from '../templates';
import type { FormTemplateConfig } from '../templates';

export const useFormFill = () => {
  const [formHtml, setFormHtml] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [templatePath, setTemplatePath] = useState('');
  const [formName, setFormName] = useState('');
  const [templateSha256, setTemplateSha256] = useState<string>();
  const [templateConfig, setTemplateConfig] = useState<FormTemplateConfig | null>(null);
  const [placeholders, setPlaceholders] = useState<string[]>([]);
  const [selectedRole, setSelectedRole] = useState('reference');
  const [draft, dispatch] = useReducer(draftReducer, undefined, createFormDraft);
  const [cccdScanning, setCccdScanning] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [validationModal, setValidationModal] = useState({
    isOpen: false, totalFields: 0, filledFields: 0, missingCount: 0,
  });
  const [toast, setToast] = useState<{
    show: boolean; message: string; variant: 'success' | 'error' | 'info';
  }>({ show: false, message: '', variant: 'info' });

  const epoch = useRef(0);
  const revision = useRef(0);
  const scanSerial = useRef(0);
  const fillSerial = useRef(0);
  const controllers = useRef<Partial<Record<'render' | 'scan' | 'fill', AbortController>>>({});
  const pending = useRef<{
    fileBytes: string; filename: string; epoch: number; revision: number;
    totalFields: number; filledFields: number;
  } | null>(null);

  useEffect(() => () => {
    epoch.current++;
    Object.values(controllers.current).forEach((controller) => controller?.abort());
  }, []);

  const updateDraft = useCallback((action: DraftAction) => {
    revision.current++;
    pending.current = null;
    setValidationModal((modal) => ({ ...modal, isOpen: false }));
    dispatch(action);
  }, []);

  const loadForm = useCallback(async (docId: string, filename: string) => {
    const currentEpoch = ++epoch.current;
    Object.values(controllers.current).forEach((controller) => controller?.abort());
    controllers.current = {};
    const controller = new AbortController();
    controllers.current.render = controller;
    const path = `forms/${docId}/${filename}`;
    setFormLoading(true);
    setFormError(null);
    setFormHtml(null);
    setTemplatePath(path);
    setFormName(filename);
    setTemplateSha256(undefined);
    setTemplateConfig(null);
    setPlaceholders([]);
    setSelectedRole('reference');
    setCccdScanning(false);
    setDownloadLoading(false);
    setToast({ show: false, message: '', variant: 'info' });
    updateDraft({ type: 'reset' });
    try {
      const { data } = await queryClient.post<FormRenderResponse>(
        ENDPOINTS.QUERY.FORMS.RENDER, { template_path: path }, { signal: controller.signal },
      );
      if (currentEpoch !== epoch.current) return;
      if (!data.success || !data.html_content) throw new Error(data.message || 'Mẫu không có nội dung');
      const fields = data.placeholders ?? [];
      const config = findTemplateConfig(data.template_sha256, fields);
      setFormHtml(data.html_content);
      setTemplateSha256(data.template_sha256);
      setPlaceholders(fields);
      setTemplateConfig(config);
      setSelectedRole(config?.roles[0]?.id ?? 'reference');
    } catch {
      if (controller.signal.aborted || currentEpoch !== epoch.current) return;
      setFormError('Không thể tải biểu mẫu. Kiểm tra kết nối và thử lại.');
    } finally {
      if (currentEpoch === epoch.current) setFormLoading(false);
    }
  }, [updateDraft]);

  const handleCCCDScan = useCallback(async (imageData: string) => {
    if (formLoading || !formHtml) return;
    const currentEpoch = epoch.current;
    const currentScan = ++scanSerial.current;
    // Capture the role before awaiting: a late response never fills another role.
    const role = selectedRole;
    const controller = new AbortController();
    controllers.current.scan?.abort();
    controllers.current.scan = controller;
    setCccdScanning(true);
    try {
      const { data } = await queryClient.post<CCCDScanResponse>(
        ENDPOINTS.QUERY.FORMS.CCCD_SCAN, { image_data: imageData, scan_mode: 'qr' }, { signal: controller.signal },
      );
      if (currentEpoch !== epoch.current || currentScan !== scanSerial.current) return;
      if (!data.success || !data.data) throw new Error('Không đọc được QR căn cước. Thử ảnh rõ hơn.');
      updateDraft({ type: 'scan', role, data: data.data, template: templateConfig });
    } catch {
      if (!controller.signal.aborted && currentEpoch === epoch.current) {
        setToast({ show: true, message: 'Không đọc được QR căn cước. Thử ảnh rõ hơn hoặc nhập bằng tay.', variant: 'error' });
      }
    } finally {
      if (currentEpoch === epoch.current && currentScan === scanSerial.current) setCccdScanning(false);
    }
  }, [formLoading, formHtml, selectedRole, templateConfig, updateDraft]);

  const resetCCCD = useCallback(() => {
    scanSerial.current++;
    controllers.current.scan?.abort();
    setCccdScanning(false);
    updateDraft({ type: 'clearScan', role: selectedRole });
  }, [selectedRole, updateDraft]);

  const handleFieldChange = useCallback((field: string, value: string) => {
    if (!placeholders.includes(field)) return;
    updateDraft({ type: 'field', field, value: value.trim() });
  }, [placeholders, updateDraft]);

  const executeDownload = useCallback(() => {
    const result = pending.current;
    pending.current = null;
    setValidationModal((modal) => ({ ...modal, isOpen: false }));
    if (!result || result.epoch !== epoch.current || result.revision !== revision.current) {
      setToast({ show: true, message: 'Bản nháp đã thay đổi. Hãy bấm tải xuống lại.', variant: 'info' });
      return;
    }
    try {
      const bytes = Uint8Array.from(atob(result.fileBytes), (char) => char.charCodeAt(0));
      const blob = new Blob([bytes], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      // Let the browser consume the URL before revoking it.
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setToast({
        show: true,
        message: `Đã tải Word: điền ${result.filledFields}/${result.totalFields} ô. Hãy kiểm tra lại trước khi sử dụng.`,
        variant: 'success',
      });
    } catch {
      setToast({ show: true, message: 'Không tạo được file tải xuống. Hãy thử lại.', variant: 'error' });
    }
  }, []);

  const handleDownload = useCallback(async () => {
    if (!templatePath || formLoading || !formHtml) return;
    const currentEpoch = epoch.current;
    const currentRevision = revision.current;
    const currentFill = ++fillSerial.current;
    const controller = new AbortController();
    controllers.current.fill?.abort();
    controllers.current.fill = controller;
    pending.current = null;
    setValidationModal((modal) => ({ ...modal, isOpen: false }));
    setDownloadLoading(true);
    try {
      const { data } = await queryClient.post<FormFillResponse>(
        ENDPOINTS.QUERY.FORMS.FILL,
        { template_path: templatePath, template_sha256: templateSha256, data: draft.values, form_name: formName },
        { signal: controller.signal },
      );
      if (currentEpoch !== epoch.current || currentFill !== fillSerial.current) return;
      if (currentRevision !== revision.current) {
        setToast({ show: true, message: 'Bạn vừa thay đổi nội dung. Hãy tải xuống lại để lấy bản mới.', variant: 'info' });
        return;
      }
      if (!data.success || !data.file_bytes) throw new Error(data.message || 'Không xuất được Word');
      const totalFields = data.total_fields ?? placeholders.length;
      const filledFields = data.filled_fields ?? 0;
      pending.current = {
        fileBytes: data.file_bytes, filename: data.filename ?? 'bieu-mau.docx',
        epoch: currentEpoch, revision: currentRevision, totalFields, filledFields,
      };
      if (filledFields < totalFields) {
        setValidationModal({ isOpen: true, totalFields, filledFields, missingCount: totalFields - filledFields });
      } else {
        executeDownload();
      }
    } catch (error) {
      if (!controller.signal.aborted && currentEpoch === epoch.current && currentFill === fillSerial.current) {
        setToast({
          show: true,
          message: error instanceof Error ? error.message : 'Không xuất được Word',
          variant: 'error',
        });
      }
    } finally {
      if (currentEpoch === epoch.current && currentFill === fillSerial.current) setDownloadLoading(false);
    }
  }, [templatePath, formLoading, formHtml, templateSha256, draft.values, formName, placeholders, executeDownload]);

  const cancelDownload = useCallback(() => {
    pending.current = null;
    setValidationModal((modal) => ({ ...modal, isOpen: false }));
  }, []);

  return {
    formHtml, formLoading, formError, templateConfig, placeholders, templatePath,
    draft, selectedRole, setSelectedRole,
    cccdData: draft.scans[selectedRole] ?? null, cccdScanning,
    validationModal, toast, setToast,
    loadForm, handleCCCDScan, resetCCCD, handleFieldChange,
    handleDownload, executeDownload, cancelDownload, downloadLoading,
  };
};
