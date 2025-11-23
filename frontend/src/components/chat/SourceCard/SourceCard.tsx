/**
 * SourceCard Component
 */

import { FileText, BookOpen, Calendar, TrendingUp } from 'lucide-react';
import { formatSimilarity } from '@/utils/formatters/number';
import styles from './SourceCard.module.css';
import type { SourceCardProps } from './SourceCard.types';

export const SourceCard = ({ source, index }: SourceCardProps) => {
  // Truncate content to 150 characters
  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className={styles.sourceCard}>
      {/* Index badge */}
      <div className={styles.badge}>{index}</div>

      {/* Content */}
      <div className={styles.content}>
        {/* Title */}
        <h4 className={styles.title}>
          <FileText size={16} />
          <span>{source.file_name}</span>
        </h4>

        {/* Metadata */}
        <div className={styles.metadata}>
          {source.ma_chuyen_nganh && (
            <span className={styles.metaItem}>
              <BookOpen size={14} />
              {source.ma_chuyen_nganh}
            </span>
          )}
          {source.ma_mon && (
            <span className={styles.metaItem}>
              <BookOpen size={14} />
              {source.ma_mon}
            </span>
          )}
          {source.nam_hoc && (
            <span className={styles.metaItem}>
              <Calendar size={14} />
              Năm {source.nam_hoc}
            </span>
          )}
        </div>

        {/* Excerpt - from first chunk */}
        {source.chunks && source.chunks.length > 0 && source.chunks[0] && (
          <p className={styles.excerpt}>{truncateText(source.chunks[0].text_content, 150)}</p>
        )}

        {/* Max Similarity score */}
        <div className={styles.score}>
          <TrendingUp size={14} />
          <span>Độ liên quan: {formatSimilarity(source.max_similarity)}</span>
        </div>
      </div>
    </div>
  );
};
