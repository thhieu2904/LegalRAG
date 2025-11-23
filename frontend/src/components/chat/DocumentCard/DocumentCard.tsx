/**
 * DocumentCard Component
 * Display a document with its chunks (grouped view)
 */

import { useState } from 'react';
import { FileText, BookOpen, ChevronDown, ChevronUp, TrendingUp } from 'lucide-react';
import { formatSimilarity } from '@/utils/formatters/number';
import { VectorComparison } from '@/components/chat/VectorComparison';
import styles from './DocumentCard.module.css';
import type { DocumentSource } from '@/types/common.types';

interface DocumentCardProps {
  document: DocumentSource;
  index: number;
  query?: string;
}

/**
 * Get upload type label in Vietnamese
 */
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

/**
 * Extract relevant snippet around keywords
 */
const extractRelevantSnippet = (
  text: string,
  query: string | undefined,
  maxLength: number = 200
): string => {
  if (!query) {
    // No query - return beginning
    return truncateAtSentence(text, maxLength);
  }

  const lowerText = text.toLowerCase();
  const keywords = query
    .toLowerCase()
    .split(' ')
    .filter((w) => w.length > 2);

  // Find first keyword occurrence
  let bestPos = -1;
  for (const kw of keywords) {
    const pos = lowerText.indexOf(kw);
    if (pos !== -1) {
      bestPos = pos;
      break;
    }
  }

  if (bestPos === -1) {
    // No keyword found - return beginning
    return truncateAtSentence(text, maxLength);
  }

  // Extract context around keyword
  const start = Math.max(0, bestPos - maxLength / 2);
  const end = Math.min(text.length, bestPos + maxLength / 2);

  let snippet = text.substring(start, end);
  if (start > 0) snippet = '...' + snippet;
  if (end < text.length) snippet = snippet + '...';

  return snippet;
};

/**
 * Truncate at sentence boundary
 */
const truncateAtSentence = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;

  const truncated = text.substring(0, maxLength);
  const lastPeriod = truncated.lastIndexOf('.');
  const lastQuestion = truncated.lastIndexOf('?');
  const lastExclaim = truncated.lastIndexOf('!');

  const boundary = Math.max(lastPeriod, lastQuestion, lastExclaim);

  if (boundary > maxLength * 0.7) {
    return truncated.substring(0, boundary + 1);
  }

  // Fallback to word boundary
  const lastSpace = truncated.lastIndexOf(' ');
  return truncated.substring(0, lastSpace) + '...';
};

export const DocumentCard = ({ document, index, query }: DocumentCardProps) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={styles.documentCard}>
      {/* Index badge */}
      <div className={styles.badge}>{index}</div>

      {/* Content */}
      <div className={styles.content}>
        {/* Document Header */}
        <div className={styles.header}>
          <h4 className={styles.title}>
            <FileText size={16} />
            <span>{document.file_name}</span>
          </h4>
          <span className={styles.uploadType}>{getUploadTypeLabel(document.upload_type)}</span>
        </div>

        {/* Metadata */}
        <div className={styles.metadata}>
          <span className={styles.metaItem}>
            <BookOpen size={14} />
            Môn: {document.ma_mon}
          </span>
          <span className={styles.metaItem}>
            <BookOpen size={14} />
            Chuyên ngành: {document.ma_chuyen_nganh}
          </span>
          {document.nam_hoc && <span className={styles.metaItem}>Năm {document.nam_hoc}</span>}
          <span className={styles.metaItem}>{document.chunk_count} đoạn văn liên quan</span>
        </div>

        {/* Similarity score */}
        <div className={styles.score}>
          <TrendingUp size={14} />
          <span>Độ liên quan: {formatSimilarity(document.max_similarity)}</span>
        </div>

        {/* Chunks preview */}
        <button onClick={() => setExpanded(!expanded)} className={styles.toggleButton}>
          {expanded ? (
            <>
              <ChevronUp size={16} />
              <span>Thu gọn</span>
            </>
          ) : (
            <>
              <ChevronDown size={16} />
              <span>Xem chi tiết {document.chunk_count} đoạn văn</span>
            </>
          )}
        </button>

        {/* Expanded chunks */}
        {expanded && document.chunks && document.chunks.length > 0 && (
          <div className={styles.chunksContainer}>
            {document.chunks.map((chunk) => (
              <div key={chunk.chunk_id} className={styles.chunkPreview}>
                <div className={styles.chunkHeader}>
                  <span className={styles.chunkIndex}>Đoạn {chunk.chunk_index + 1}</span>
                  <span className={styles.chunkSimilarity}>
                    {formatSimilarity(chunk.similarity)}
                  </span>
                </div>
                <p className={styles.chunkContent}>
                  {extractRelevantSnippet(chunk.text_content, query, 200)}
                </p>

                {/* Vector Comparison (if embeddings available) */}
                {chunk.query_embedding && chunk.chunk_embedding && (
                  <VectorComparison
                    queryEmbedding={chunk.query_embedding}
                    chunkEmbedding={chunk.chunk_embedding}
                    similarity={chunk.similarity}
                    queryText={query || ''}
                    chunkText={chunk.text_content}
                  />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
