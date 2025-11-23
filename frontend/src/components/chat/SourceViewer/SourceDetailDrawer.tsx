/**
 * SourceDetailDrawer Component
 * Show detailed chunks of a single source
 */

import { useState } from 'react';
import { ChevronLeft, TrendingUp, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { formatSimilarity } from '@/utils/formatters/number';
import styles from './SourceDetailDrawer.module.css';
import type { DocumentSource } from '@/types/common.types';

interface SourceDetailDrawerProps {
  source: DocumentSource;
  query?: string;
  onBack: () => void;
}

/**
 * Extract relevant snippet around keywords (short version for preview)
 */
const extractRelevantSnippet = (
  text: string,
  query: string | undefined,
  maxLength: number = 250
): string => {
  if (!query) {
    return truncateAtSentence(text, maxLength);
  }

  const lowerText = text.toLowerCase();
  const keywords = query
    .toLowerCase()
    .split(' ')
    .filter((w) => w.length > 2);

  let bestPos = -1;
  for (const kw of keywords) {
    const pos = lowerText.indexOf(kw);
    if (pos !== -1) {
      bestPos = pos;
      break;
    }
  }

  if (bestPos === -1) {
    return truncateAtSentence(text, maxLength);
  }

  const start = Math.max(0, bestPos - maxLength / 2);
  const end = Math.min(text.length, bestPos + maxLength / 2);

  let snippet = text.substring(start, end);
  if (start > 0) snippet = '...' + snippet;
  if (end < text.length) snippet = snippet + '...';

  return snippet;
};

/**
 * Clean up text content (remove extra spaces, dots at start)
 */
const cleanTextContent = (text: string): string => {
  return text
    .replace(/^\.\s+/, '') // Remove leading dot
    .replace(/\s+/g, ' ') // Collapse multiple spaces
    .trim();
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

  const lastSpace = truncated.lastIndexOf(' ');
  return truncated.substring(0, lastSpace) + '...';
};

/**
 * Highlight keywords in text
 */
const highlightKeywords = (
  text: string,
  query: string | undefined
): (string | React.ReactElement)[] => {
  if (!query) return [text];

  const keywords = query
    .toLowerCase()
    .split(' ')
    .filter((w) => w.length > 2);
  if (keywords.length === 0) return [text];

  const lowerText = text.toLowerCase();
  const matches: Array<{ start: number; end: number; word: string }> = [];

  keywords.forEach((kw) => {
    let pos = 0;
    while ((pos = lowerText.indexOf(kw, pos)) !== -1) {
      matches.push({
        start: pos,
        end: pos + kw.length,
        word: text.substring(pos, pos + kw.length),
      });
      pos += kw.length;
    }
  });

  if (matches.length === 0) return [text];

  matches.sort((a, b) => a.start - b.start);

  const result: (string | React.ReactElement)[] = [];
  let lastIndex = 0;

  matches.forEach((match, idx) => {
    if (match.start > lastIndex) {
      result.push(text.substring(lastIndex, match.start));
    }
    result.push(<mark key={`mark-${idx}`}>{match.word}</mark>);
    lastIndex = match.end;
  });

  if (lastIndex < text.length) {
    result.push(text.substring(lastIndex));
  }

  return result;
};

export const SourceDetailDrawer = ({ source, query, onBack }: SourceDetailDrawerProps) => {
  const [expandedChunks, setExpandedChunks] = useState<Set<string>>(new Set());

  const toggleChunkExpanded = (chunkId: string) => {
    const newExpanded = new Set(expandedChunks);
    if (newExpanded.has(chunkId)) {
      newExpanded.delete(chunkId);
    } else {
      newExpanded.add(chunkId);
    }
    setExpandedChunks(newExpanded);
  };

  return (
    <div className={styles.drawer}>
      {/* Overlay */}
      <div className={styles.overlay} onClick={onBack} />

      {/* Drawer Content */}
      <div className={styles.content}>
        {/* Header */}
        <div className={styles.header}>
          <button onClick={onBack} className={styles.backButton} aria-label="Quay lại">
            <ChevronLeft size={24} />
          </button>
          <div className={styles.headerTitle}>
            <h2 className={styles.title}>{source.file_name}</h2>
            <p className={styles.subtitle}>{source.chunk_count} đoạn văn</p>
          </div>
        </div>

        {/* Metadata */}
        <div className={styles.metadata}>
          <span className={styles.metaItem}>
            <BookOpen size={14} />
            {source.ma_mon}
          </span>
          <span className={styles.metaItem}>
            <TrendingUp size={14} />
            Độ liên quan: {formatSimilarity(source.max_similarity)}
          </span>
        </div>

        {/* Chunks */}
        <div className={styles.chunksContainer}>
          <h3 className={styles.chunksTitle}>Các đoạn văn liên quan</h3>

          {source.chunks && source.chunks.length > 0 ? (
            <div className={styles.chunks}>
              {source.chunks.map((chunk) => {
                const isExpanded = expandedChunks.has(chunk.chunk_id);
                const fullContent = cleanTextContent(chunk.text_content);
                const previewContent = extractRelevantSnippet(fullContent, query, 250);
                const isFullContentLonger =
                  fullContent.length >
                  previewContent.replace(/^\.\.\./g, '').replace(/\.\.\.$/g, '').length;

                return (
                  <div key={chunk.chunk_id} className={styles.chunk}>
                    {/* Chunk header */}
                    <div className={styles.chunkHeader}>
                      <span className={styles.chunkNumber}>Đoạn {chunk.chunk_index + 1}</span>
                      <span className={styles.chunkScore}>
                        {formatSimilarity(chunk.similarity)}
                      </span>
                    </div>

                    {/* Chunk content - Preview or Full */}
                    <p className={styles.chunkContent}>
                      {highlightKeywords(isExpanded ? fullContent : previewContent, query)}
                    </p>

                    {/* Expand/Collapse button if content is longer */}
                    {isFullContentLonger && (
                      <button
                        onClick={() => toggleChunkExpanded(chunk.chunk_id)}
                        className={styles.expandButton}
                      >
                        {isExpanded ? (
                          <>
                            <ChevronUp size={16} />
                            Thu gọn
                          </>
                        ) : (
                          <>
                            <ChevronDown size={16} />
                            Xem thêm
                          </>
                        )}
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className={styles.noChunks}>Không có dữ liệu chi tiết</p>
          )}
        </div>
      </div>
    </div>
  );
};
