/**
 * FormViewer Component - Rewritten with createRoot pattern
 *
 * Key differences from previous approach:
 * 1. Uses createRoot to hydrate each placeholder as independent React component
 * 2. HTML set via ref.innerHTML (not dangerouslySetInnerHTML) to prevent React re-render
 * 3. EditablePlaceholder uses popover for editing - avoids focus issues completely
 *
 * This follows the stable pattern from frontend_old/FormRenderer.tsx
 */

import { useEffect, useRef, useCallback } from 'react';
import { createRoot } from 'react-dom/client';
import type { Root } from 'react-dom/client';
import { Download, Loader, AlertCircle, FileText } from 'lucide-react';
import { EditablePlaceholder } from './EditablePlaceholder';
import styles from './FormViewer.module.css';

interface FormViewerProps {
  html: string | null;
  loading: boolean;
  error: string | null;
  onFieldChange: (fieldName: string, value: string) => void;
  onDownload: () => void;
  downloadLoading: boolean;
  formFilename?: string;
}

export const FormViewer = ({
  html,
  loading,
  error,
  onFieldChange,
  onDownload,
  downloadLoading,
}: FormViewerProps) => {
  // Refs for managing React roots and state
  const formContentRef = useRef<HTMLDivElement>(null);
  const reactRootsRef = useRef<Map<HTMLElement, Root>>(new Map());
  const isHydratedRef = useRef(false);
  const htmlSetRef = useRef(false);
  const formDataRef = useRef<Record<string, string>>({});

  // Store callbacks in refs to avoid dependency issues
  const onFieldChangeRef = useRef(onFieldChange);
  onFieldChangeRef.current = onFieldChange;

  // Cleanup React roots on unmount
  useEffect(() => {
    const currentRoots = reactRootsRef.current;
    return () => {
      currentRoots.forEach((root, element) => {
        try {
          element.classList.remove('react-hydrated');
          root.unmount();
        } catch (e) {
          console.warn('Error unmounting React root:', e);
        }
      });
      currentRoots.clear();
      isHydratedRef.current = false;
    };
  }, []);

  // Get field value helper
  const getFieldValue = useCallback((fieldName: string): string => {
    return formDataRef.current[fieldName] || '';
  }, []);

  // Handle save from EditablePlaceholder
  const handleFieldSave = useCallback((fieldName: string, value: string) => {
    formDataRef.current[fieldName] = value;
    onFieldChangeRef.current(fieldName, value);
  }, []);

  // Hydrate placeholders with React components
  const hydratePlaceholders = useCallback(() => {
    if (isHydratedRef.current) {
      console.log('⏭️ Skipping hydration - already hydrated');
      return;
    }

    const formContainer = formContentRef.current;
    if (!formContainer) {
      console.warn('⚠️ Form container not found');
      return;
    }

    console.log('🔄 Starting placeholder hydration...');

    // Find all placeholders with field_ prefix (unified naming)
    const placeholders = formContainer.querySelectorAll(
      '[class*="placeholder_field_"], [class*="placeholder_"]'
    );

    console.log(`📍 Found ${placeholders.length} placeholders to hydrate`);

    let hydratedCount = 0;

    placeholders.forEach((element) => {
      const htmlElement = element as HTMLElement;

      // Extract field name from class
      const className = Array.from(htmlElement.classList).find((cls) =>
        cls.startsWith('placeholder_')
      );
      if (!className) return;

      // Parse field name
      const fieldName = className.replace('placeholder_', '');

      // Skip if already hydrated
      if (reactRootsRef.current.has(htmlElement)) {
        console.log(`⏭️ Already hydrated: ${fieldName}`);
        return;
      }

      try {
        // Create React root
        const root = createRoot(htmlElement);
        reactRootsRef.current.set(htmlElement, root);
        htmlElement.classList.add('react-hydrated');

        // Render EditablePlaceholder
        root.render(
          <EditablePlaceholder
            fieldName={fieldName}
            value={getFieldValue(fieldName)}
            onSave={handleFieldSave}
            placeholder={`Nhập ${fieldName.replace(/_/g, ' ')}`}
          />
        );

        hydratedCount++;
        console.log(`✅ Hydrated: ${fieldName}`);
      } catch (err) {
        console.error(`❌ Error hydrating ${fieldName}:`, err);
      }
    });

    if (hydratedCount > 0) {
      isHydratedRef.current = true;
      console.log(`✅ Hydration complete - ${hydratedCount} elements`);
    }
  }, [getFieldValue, handleFieldSave]);

  // Effect: Set HTML content once and hydrate
  useEffect(() => {
    if (html && !loading && formContentRef.current && !htmlSetRef.current) {
      console.log('🎯 Setting HTML content');

      // Set HTML directly via ref (not dangerouslySetInnerHTML)
      formContentRef.current.innerHTML = html;
      htmlSetRef.current = true;

      // Hydrate after DOM update
      setTimeout(() => {
        hydratePlaceholders();
      }, 100);
    }
  }, [html, loading, hydratePlaceholders]);

  // Loading state
  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingState}>
          <Loader className={styles.spinner} size={40} />
          <p className={styles.loadingText}>Đang tải biểu mẫu...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.errorState}>
          <AlertCircle size={40} className={styles.errorIcon} />
          <p className={styles.errorTitle}>Không thể tải biểu mẫu</p>
          <p className={styles.errorText}>{error}</p>
        </div>
      </div>
    );
  }

  // Empty state
  if (!html) {
    return (
      <div className={styles.container}>
        <div className={styles.emptyState}>
          <FileText size={40} className={styles.emptyIcon} />
          <p className={styles.emptyText}>Chưa có biểu mẫu để hiển thị</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <FileText size={20} />
          <h2 className={styles.title}>Biểu mẫu</h2>
        </div>
        <div className={styles.headerRight}>
          <button onClick={onDownload} disabled={downloadLoading} className={styles.downloadButton}>
            {downloadLoading ? (
              <>
                <Loader className={styles.spinner} size={16} />
                <span>Đang tải...</span>
              </>
            ) : (
              <>
                <Download size={16} />
                <span>Tải xuống</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Form Content - NO dangerouslySetInnerHTML */}
      <div className={styles.formContent}>
        <div ref={formContentRef} className={styles.formHTML} />
      </div>

      {/* Footer Info */}
      <div className={styles.footer}>
        <AlertCircle size={16} />
        <p className={styles.footerText}>Click vào các ô được đánh dấu để chỉnh sửa nội dung.</p>
      </div>
    </div>
  );
};
