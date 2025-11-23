/**
 * SourceList Component
 */

import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { DocumentCard } from '../DocumentCard';
import styles from './SourceList.module.css';
import type { SourceListProps } from './SourceList.types';

export const SourceList = ({ sources, query }: SourceListProps) => {
  const [expanded, setExpanded] = useState(false);
  const displaySources = expanded ? sources : sources.slice(0, 3);
  const hasMore = sources.length > 3;

  if (sources.length === 0) return null;

  return (
    <div className={styles.sourceList}>
      {/* Header */}
      <div className={styles.header}>
        <FileText size={16} />
        <span className={styles.headerText}>Nguồn tham khảo ({sources.length})</span>
      </div>

      {/* Sources */}
      <div className={styles.sources}>
        {displaySources.map((document, idx) => (
          <DocumentCard
            key={document.document_id}
            document={document}
            index={idx + 1}
            query={query}
          />
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
              <span>Xem thêm {sources.length - 3} nguồn</span>
            </>
          )}
        </button>
      )}
    </div>
  );
};
