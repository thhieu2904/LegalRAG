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
            {formFilename ? decodeURIComponent(formFilename) : 'Đang tải...'}
          </p>
        </div>

        {/* 2-Column Layout */}
        <div className={styles.content}>
          {/* Left Column: CCCD Scanner - Display only, no auto-fill */}
          <div className={styles.leftColumn}>
            <CCCDScanner
              cccdData={cccdData}
              scanning={cccdScanning}
              onScan={handleCCCDScan}
              onReset={resetCCCD}
            />
          </div>

          {/* Right Column: Form Viewer */}
          <div className={styles.rightColumn}>
            <FormViewer
              html={formHtml}
              loading={formLoading}
              error={formError}
              onFieldChange={handleFieldChange}
              onDownload={handleDownload}
              downloadLoading={downloadLoading}
              formFilename={formFilename}
            />
          </div>
        </div>
      </main>

      {/* Validation Modal */}
      <ConfirmModal
        isOpen={validationModal.isOpen}
        onClose={() => setValidationModal({ ...validationModal, isOpen: false })}
        onConfirm={() => {
          setValidationModal({ ...validationModal, isOpen: false });
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
