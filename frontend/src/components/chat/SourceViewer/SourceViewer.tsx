/**
 * SourceViewer Component
 * Modal/Drawer to view detailed sources
 */

import { useState } from 'react';
import { X, ChevronRight, TrendingUp } from 'lucide-react';
import { formatSimilarity } from '@/utils/formatters/number';
import { SourceDetailDrawer } from './SourceDetailDrawer';
import styles from './SourceViewer.module.css';
import type { DocumentSource } from '@/types/common.types';

interface SourceViewerProps {
  sources: DocumentSource[];
  query?: string;
  onClose: () => void;
}

const getUploadTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    chuyen_nganh: 'Chuyên ngành',
    de_cuong_mon: 'Đề cương môn',
    bai_giang: 'Bài giảng',
    tai_lieu: 'Tài liệu',
    bai_tap: 'Bài tập',
    de_thi: 'Đề thi',
    q_and_a: 'Hỏi đáp',
  };
  return labels[type] || type;
};

export const SourceViewer = ({ sources, query, onClose }: SourceViewerProps) => {
  const [selectedSource, setSelectedSource] = useState<DocumentSource | null>(null);

  if (selectedSource) {
    return (
      <SourceDetailDrawer
        source={selectedSource}
        query={query}
        onBack={() => setSelectedSource(null)}
      />
    );
  }

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>Nguồn tham khảo</h2>
            <p className={styles.subtitle}>{sources.length} tài liệu được tìm thấy</p>
          </div>
          <button onClick={onClose} className={styles.closeButton} aria-label="Đóng">
            <X size={24} />
          </button>
        </div>

        {/* Sources List */}
        <div className={styles.sourcesList}>
          {sources.map((source, idx) => (
            <button
              key={source.document_id}
              onClick={() => setSelectedSource(source)}
              className={styles.sourceItem}
            >
              {/* Index */}
              <span className={styles.index}>{idx + 1}</span>

              {/* Info */}
              <div className={styles.info}>
                <div className={styles.titleRow}>
                  <span className={styles.fileName}>{source.file_name}</span>
                  <span className={styles.uploadType}>
                    {getUploadTypeLabel(source.upload_type)}
                  </span>
                </div>
                <div className={styles.metaRow}>
                  <span className={styles.meta}>{source.ma_mon}</span>
                  {source.chunk_count && (
                    <span className={styles.meta}>{source.chunk_count} đoạn</span>
                  )}
                </div>
              </div>

              {/* Similarity score */}
              <div className={styles.score}>
                <TrendingUp size={14} />
                <span>{formatSimilarity(source.max_similarity)}</span>
              </div>

              {/* Arrow */}
              <ChevronRight size={20} className={styles.arrow} />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
