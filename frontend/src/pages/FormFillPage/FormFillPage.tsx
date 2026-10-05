/**
 * FormFillPage - Modern form filling page
 *
 * Architecture:
 * - Uses MainLayout for Header/Footer
 * - Content: 2-column layout
 *   - Left: CCCD Scanner
 *   - Right: Form Viewer with auto-fill
 *
 * Flow:
 * 1. Load form from URL params (docId, formFilename)
 * 2. Render form HTML (via query-service /forms/render)
 * 3. Scan CCCD (optional)
 * 4. Auto-fill form fields
 * 5. Allow manual edits
 * 6. Download filled form
 */

import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { CCCDScanner } from './components/CCCDScanner';
import { FormViewer } from './components';
import { useFormFill } from './hooks/useFormFill';
import { ConfirmModal } from '@/components/common/ConfirmModal';
import { ToastItem } from '@/components/common/Toast';
import styles from './FormFillPage.module.css';

export const FormFillPage = () => {
  const navigate = useNavigate();
  const { docId, formFilename } = useParams<{
    docId: string;
    formFilename: string;
  }>();

  const {
    // Form state
    formHtml,
    formLoading,
    formError,
    templateConfig,
    templatePath,
    placeholders,
    draft,
    selectedRole,
    setSelectedRole,

    // CCCD state
    cccdData,
    cccdScanning,

    // Modal/Toast state
    validationModal,
    toast,
    setToast,

    // Actions
    loadForm,
    handleCCCDScan,
    resetCCCD,
    handleFieldChange,
    handleDownload,
    executeDownload,
    cancelDownload,
    downloadLoading,
  } = useFormFill();

  // Load form on mount
  useEffect(() => {
    if (docId && formFilename) {
      loadForm(docId, formFilename);
    }
  }, [docId, formFilename, loadForm]);

  // Handle back navigation
  const handleBack = () => {
    navigate(-1);
  };

  return (
    <div className={styles.container}>
      {/* Main Content */}
      <main className={styles.main}>
        {/* Back Button */}
        <button onClick={handleBack} className={styles.backButton}>
          <ArrowLeft size={20} />
          <span>Quay lại</span>
        </button>

        {/* Page Title */}
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>Điền Biểu Mẫu</h1>
          <p className={styles.pageSubtitle}>
            {formFilename ?? 'Đang tải...'}
          </p>
        </div>

        {/* 2-Column Layout */}
        <div className={styles.content}>
          {/* Role-aware QR mapping. Unknown files remain manual-only. */}
          <div className={styles.leftColumn}>
            <section className={styles.mappingPanel} aria-label="Cấu hình điền mẫu">
              <h2>{templateConfig?.name ?? 'Điền mẫu thủ công'}</h2>
              {templateConfig ? (
                <>
                  {templateConfig.roles.length > 1 ? (
                    <>
                      <label htmlFor="scan-role">QR này thuộc người nào?</label>
                      <select id="scan-role" value={selectedRole} disabled={formLoading || cccdScanning} onChange={(event) => setSelectedRole(event.target.value)}>
                        {templateConfig.roles.map((role) => <option key={role.id} value={role.id}>{role.label}</option>)}
                      </select>
                    </>
                  ) : (
                    <p>Quét căn cước của người yêu cầu để điền họ tên, ngày sinh, nơi cư trú và số căn cước.</p>
                  )}
                  <p>Ô đã chỉnh được giữ nguyên. Các ô còn lại có thể gõ hoặc bấm mic để nói.</p>
                </>
              ) : !formLoading && formHtml && (
                <p>Mẫu này chưa khớp cấu hình đã kiểm tra. Bạn vẫn có thể gõ hoặc nói từng ô; QR chỉ dùng để tham khảo, không tự điền.</p>
              )}
              {draft.scanReport?.role === selectedRole && <p role="status">QR đã điền {draft.scanReport.applied} ô; giữ nguyên {draft.scanReport.protected} ô có dữ liệu khác.</p>}
              <p>Đã điền {placeholders.filter((field) => draft.values[field]?.trim()).length}/{placeholders.length} ô.</p>
              <p>Bản nháp chỉ giữ trong phiên trang. Tải Word không tự lưu hồ sơ lên server.</p>
            </section>
            <CCCDScanner
              key={templatePath}
              cccdData={cccdData}
              scanning={cccdScanning}
              onScan={handleCCCDScan}
              onReset={resetCCCD}
            />
          </div>

          {/* Right Column: Form Viewer */}
          <div className={styles.rightColumn}>
            <FormViewer
              key={templatePath}
              html={formHtml}
              loading={formLoading}
              error={formError}
              draft={draft}
              templateConfig={templateConfig}
              onFieldChange={handleFieldChange}
              onDownload={handleDownload}
              downloadLoading={downloadLoading}
            />
          </div>
        </div>
      </main>

      {/* Validation Modal */}
      <ConfirmModal
        isOpen={validationModal.isOpen}
        onClose={cancelDownload}
        onConfirm={() => {
          executeDownload(); // Execute download with stored data
        }}
        title="Biểu mẫu chưa điền đầy đủ"
        message={
          <>
            <p style={{ marginBottom: '12px' }}>
              Đã điền:{' '}
              <strong>
                {validationModal.filledFields}/{validationModal.totalFields}
              </strong>{' '}
              trường
            </p>
            <p style={{ marginBottom: '12px' }}>
              Còn thiếu: <strong>{validationModal.missingCount}</strong> trường chưa điền
            </p>
            <p style={{ color: '#6b7280', fontSize: '13px' }}>
              💡 Lưu ý: Các trường còn thiếu có thể điền bằng tay sau khi tải về.
            </p>
          </>
        }
        confirmText="Tải xuống"
        cancelText="Hủy"
        variant="warning"
      />

      {/* Toast Notification */}
      {toast.show && (
        <ToastItem
          id="form-toast"
          message={toast.message}
          type={toast.variant}
          onClose={() => setToast({ ...toast, show: false })}
        />
      )}
    </div>
  );
};

export default FormFillPage;
