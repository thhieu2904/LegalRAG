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

    // Actions
    loadForm,
    handleCCCDScan,
    resetCCCD,
    handleFieldChange,
    handleDownload,
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
    </div>
  );
};

export default FormFillPage;
