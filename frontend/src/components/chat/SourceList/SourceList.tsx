/**
 * SourceList Component - Display legal document sources with download
 * Shows document titles, relevance scores, and attached forms
 */

import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Scale, Download, FileIcon } from 'lucide-react';
import { STORAGE_SERVICE_URL } from '@/services/api/client';
import styles from './SourceList.module.css';
import type { SourceListProps } from './SourceList.types';

export const SourceList = ({ sources, forms }: SourceListProps) => {
  const [expanded, setExpanded] = useState(false);

  // Group sources by document_title to avoid duplicates
  const uniqueDocuments = sources.reduce(
    (acc, source) => {
      const title = source.document_title || 'Văn bản pháp luật';
      if (!acc.find((d) => d.title === title)) {
        acc.push({
          title,
          similarity: source.similarity,
          file_path: source.file_path,
        });
      }
      return acc;
    },
    [] as Array<{ title: string; similarity: number; file_path?: string }>
  );

  const displayDocs = expanded ? uniqueDocuments : uniqueDocuments.slice(0, 2);
  const hasMore = uniqueDocuments.length > 2;

  // Handle document download
  const handleDownloadDocument = (filePath: string, title: string) => {
    const downloadUrl = `${STORAGE_SERVICE_URL}/download?file_path=${encodeURIComponent(filePath)}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `${title}.pdf`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle form download
  const handleDownloadForm = (templatePath: string, formName: string) => {
    const downloadUrl = `${STORAGE_SERVICE_URL}/download?file_path=${encodeURIComponent(templatePath)}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = formName;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (uniqueDocuments.length === 0) return null;

  return (
    <div className={styles.sourceList}>
      {/* Header */}
      <div className={styles.header}>
        <Scale size={16} />
        <span className={styles.headerText}>Văn bản tham khảo ({uniqueDocuments.length})</span>
      </div>

      {/* Documents */}
      <div className={styles.sources}>
        {displayDocs.map((doc, idx) => (
          <div key={idx} className={styles.sourceCard}>
            <div className={styles.documentInfo}>
              <span className={styles.documentTitle}>
                <FileText size={14} />
                {doc.title}
              </span>
              <span className={styles.similarity}>
                Độ tương đồng: {(doc.similarity * 100).toFixed(0)}%
              </span>
            </div>
            {doc.file_path && (
              <button
                className={styles.downloadBtn}
                onClick={() => handleDownloadDocument(doc.file_path!, doc.title)}
                title="Tải văn bản PDF"
              >
                <Download size={14} />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Show more/less button */}
      {hasMore && (
        <button onClick={() => setExpanded(!expanded)} className={styles.toggleButton}>
          {expanded ? (
            <>
              <ChevronUp size={16} />
              <span>Thu gọn</span>
            </>
          ) : (
            <>
              <ChevronDown size={16} />
              <span>Xem thêm {uniqueDocuments.length - 2} văn bản</span>
            </>
          )}
        </button>
      )}

      {/* Forms Section */}
      {forms && forms.length > 0 && (
        <div className={styles.formsSection}>
          <div className={styles.formsHeader}>
            <FileIcon size={14} />
            <span>Biểu mẫu đính kèm ({forms.length})</span>
          </div>
          <div className={styles.formsList}>
            {forms.map((form) => (
              <div key={form.id} className={styles.formItem}>
                <span className={styles.formName}>{form.form_name}</span>
                {form.template_path && (
                  <button
                    className={styles.downloadBtn}
                    onClick={() => handleDownloadForm(form.template_path!, form.form_name)}
                    title="Tải biểu mẫu"
                  >
                    <Download size={14} />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
