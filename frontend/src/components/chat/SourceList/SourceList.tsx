/**
 * SourceList Component - Display legal document sources
 * Shows document titles and relevance scores
 */

import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Scale } from 'lucide-react';
import styles from './SourceList.module.css';
import type { SourceListProps } from './SourceList.types';

export const SourceList = ({ sources }: SourceListProps) => {
  const [expanded, setExpanded] = useState(false);

  // Group sources by document_title to avoid duplicates
  const uniqueDocuments = sources.reduce(
    (acc, source) => {
      const title = source.document_title || 'Văn bản pháp luật';
      if (!acc.find((d) => d.title === title)) {
        acc.push({
          title,
          similarity: source.similarity,
          preview: source.content.substring(0, 150) + '...',
        });
      }
      return acc;
    },
    [] as Array<{ title: string; similarity: number; preview: string }>
  );

  const displayDocs = expanded ? uniqueDocuments : uniqueDocuments.slice(0, 2);
  const hasMore = uniqueDocuments.length > 2;

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
            <div className={styles.sourceHeader}>
              <span className={styles.documentTitle}>
                <FileText size={14} />
                {doc.title}
              </span>
              <span className={styles.similarity}>
                {(doc.similarity * 100).toFixed(0)}% phù hợp
              </span>
            </div>
            <div className={styles.sourceContent}>{doc.preview}</div>
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
    </div>
  );
};
