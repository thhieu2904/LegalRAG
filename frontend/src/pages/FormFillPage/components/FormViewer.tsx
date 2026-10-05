import { useCallback, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { Download, Loader, AlertCircle, FileText } from 'lucide-react';
import { EditablePlaceholder } from './EditablePlaceholder';
import type { FormDraft } from '../draft';
import { qrValuesForRole } from '../draft';
import type { FormTemplateConfig } from '../templates';
import styles from './FormViewer.module.css';

interface FormViewerProps {
  html: string | null;
  loading: boolean;
  error: string | null;
  draft: FormDraft;
  templateConfig: FormTemplateConfig | null;
  onFieldChange: (fieldName: string, value: string) => void;
  onDownload: () => void;
  downloadLoading: boolean;
}

/** Only document markup, never executable HTML from an uploaded document. */
function safeDocumentHtml(html: string): string {
  const parsed = new DOMParser().parseFromString(html, 'text/html');
  parsed.querySelectorAll('script,iframe,object,embed,link,meta,base,form,input,button,textarea,svg').forEach((node) => node.remove());
  parsed.body.querySelectorAll('*').forEach((element) => {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim();
      if (name.startsWith('on') || name === 'srcdoc' || name === 'formaction'
        || (name === 'style' && /url\s*\(|expression\s*\(|@import/i.test(value))) {
        element.removeAttribute(attribute.name);
      }
      if (name === 'href' && !/^(https?:|mailto:|tel:|#|\/)/i.test(value)) element.removeAttribute(name);
      if (name === 'src' && !/^data:image\/(png|jpeg|gif|webp);base64,/i.test(value)) element.removeAttribute(name);
    }
    if (element.tagName === 'A') element.setAttribute('rel', 'noopener noreferrer');
  });
  return parsed.body.innerHTML;
}

function HtmlFields({ html, draft, templateConfig, onFieldChange }: {
  html: string;
  draft: FormDraft;
  templateConfig: FormTemplateConfig | null;
  onFieldChange: FormViewerProps['onFieldChange'];
}) {
  const [targets, setTargets] = useState<{ element: HTMLElement; field: string }[]>([]);
  const attachHtml = useCallback((node: HTMLDivElement | null) => {
    if (!node) return;
    node.innerHTML = safeDocumentHtml(html);
    const fields: { element: HTMLElement; field: string }[] = [];
    node.querySelectorAll<HTMLElement>('[class*="placeholder_"]').forEach((element) => {
      const marker = Array.from(element.classList).find((name) => /^placeholder_[A-Za-z][A-Za-z0-9_]*$/.test(name));
      if (marker) {
        element.textContent = '';
        fields.push({ element, field: marker.slice('placeholder_'.length) });
      }
    });
    setTargets(fields);
  }, [html]);

  const suggestions = useMemo(() => {
    const values: Record<string, string> = {};
    for (const [role, scan] of Object.entries(draft.scans)) {
      Object.assign(values, qrValuesForRole(templateConfig, role, scan));
    }
    return values;
  }, [draft.scans, templateConfig]);

  return (
    <>
      <div ref={attachHtml} className={styles.formHTML} />
      {targets.map(({ element, field }, index) => createPortal(
        <EditablePlaceholder
          fieldName={field}
          value={draft.values[field] ?? ''}
          config={templateConfig?.fields.find((item) => item.id === field)}
          fromQr={draft.sources[field] === 'qr'}
          cccdValue={suggestions[field]}
          onSave={onFieldChange}
        />,
        element,
        `${field}:${index}`,
      ))}
    </>
  );
}

export const FormViewer = ({
  html, loading, error, draft, templateConfig, onFieldChange, onDownload, downloadLoading,
}: FormViewerProps) => {
  if (loading) return (
    <div className={styles.container}><div className={styles.loadingState}>
      <Loader className={styles.spinner} size={40} /><p className={styles.loadingText}>Đang tải biểu mẫu...</p>
    </div></div>
  );
  if (error) return (
    <div className={styles.container}><div className={styles.errorState}>
      <AlertCircle size={40} className={styles.errorIcon} />
      <p className={styles.errorTitle}>Không thể tải biểu mẫu</p><p className={styles.errorText}>{error}</p>
    </div></div>
  );
  if (!html) return (
    <div className={styles.container}><div className={styles.emptyState}>
      <FileText size={40} className={styles.emptyIcon} /><p>Chưa có biểu mẫu để hiển thị</p>
    </div></div>
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}><FileText size={20} /><h2 className={styles.title}>Biểu mẫu</h2></div>
        <button type="button" onClick={onDownload} disabled={downloadLoading} className={styles.downloadButton}>
          {downloadLoading ? <Loader className={styles.spinner} size={16} /> : <Download size={16} />}
          {downloadLoading ? 'Đang xuất Word…' : 'Tải Word'}
        </button>
      </div>
      <div className={styles.formContent}>
        <HtmlFields key={html} html={html} draft={draft} templateConfig={templateConfig} onFieldChange={onFieldChange} />
      </div>
      <div className={styles.footer}>
        <AlertCircle size={16} />
        <p className={styles.footerText}>Bấm ô được đánh dấu để gõ hoặc nói. Đây là bản xem nội dung; hãy kiểm tra bố cục trong Word sau khi xuất.</p>
      </div>
    </div>
  );
};
