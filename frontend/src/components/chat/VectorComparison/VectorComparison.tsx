/**
 * VectorComparison Component
 * Display visual comparison between query and chunk vectors
 */

import { TrendingUp } from 'lucide-react';
import { formatSimilarity } from '@/utils/formatters/number';
import styles from './VectorComparison.module.css';

interface VectorComparisonProps {
  queryEmbedding: number[];
  chunkEmbedding: number[];
  similarity: number;
  queryText: string;
  chunkText: string;
}

export const VectorComparison = ({
  queryEmbedding,
  chunkEmbedding,
  similarity,
  queryText,
  chunkText,
}: VectorComparisonProps) => {
  // Visualize subset of vector (first 20 dimensions for simplicity)
  const displayDims = 20;
  const querySubset = queryEmbedding.slice(0, displayDims);
  const chunkSubset = chunkEmbedding.slice(0, displayDims);

  return (
    <div className={styles.vectorComparison}>
      {/* Header */}
      <div className={styles.header}>
        <span className={styles.title}>🧮 Vector Comparison</span>
        <span className={styles.similarity}>
          <TrendingUp size={14} />
          Độ tương đồng: {formatSimilarity(similarity)}
        </span>
      </div>

      {/* Text Preview */}
      <div className={styles.textPreview}>
        <div className={styles.textRow}>
          <div className={styles.label}>Query:</div>
          <div className={styles.text}>{queryText}</div>
        </div>
        <div className={styles.textRow}>
          <div className={styles.label}>Chunk:</div>
          <div className={styles.text}>{chunkText.substring(0, 100)}...</div>
        </div>
      </div>

      {/* Vector Visualization (Bar chart) */}
      <div className={styles.vectorViz}>
        <div className={styles.vectorLabel}>
          Vector Values (First {displayDims} / {queryEmbedding.length} dimensions)
        </div>
        <div className={styles.barsContainer}>
          {querySubset.map((value, idx) => {
            const chunkValue = chunkSubset[idx] ?? 0;
            const maxVal = Math.max(Math.abs(value), Math.abs(chunkValue), 0.1);
            const queryHeight = (Math.abs(value) / maxVal) * 100;
            const chunkHeight = (Math.abs(chunkValue) / maxVal) * 100;

            return (
              <div key={idx} className={styles.barPair}>
                {/* Query bar */}
                <div
                  className={`${styles.bar} ${styles.queryBar}`}
                  style={{
                    height: `${queryHeight}%`,
                    opacity: 0.8,
                  }}
                  title={`Dim ${idx}: Query=${value.toFixed(3)}, Chunk=${chunkValue.toFixed(3)}`}
                />
                {/* Chunk bar */}
                <div
                  className={`${styles.bar} ${styles.chunkBar}`}
                  style={{
                    height: `${chunkHeight}%`,
                    opacity: 0.8,
                  }}
                  title={`Dim ${idx}: Chunk=${chunkValue.toFixed(3)}`}
                />
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className={styles.legend}>
          <div className={styles.legendItem}>
            <div className={`${styles.legendBox} ${styles.queryBox}`} />
            <span>Query Vector</span>
          </div>
          <div className={styles.legendItem}>
            <div className={`${styles.legendBox} ${styles.chunkBox}`} />
            <span>Chunk Vector</span>
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div className={styles.explanation}>
        <strong>💡 Tại sao {formatSimilarity(similarity)}?</strong>
        <p>
          Cosine similarity giữa 2 vector {queryEmbedding.length} chiều = {similarity.toFixed(4)}.
          Nghĩa là ngữ cảnh tương tự <strong>{(similarity * 100).toFixed(0)}%</strong>, dựa trên AI
          hiểu ngôn ngữ (không chỉ khớp từ khóa).
        </p>
        <p className={styles.note}>
          Đang hiển thị {displayDims} / {queryEmbedding.length} chiều đầu tiên để dễ quan sát. So
          sánh thực tế sử dụng tất cả {queryEmbedding.length} chiều.
        </p>
      </div>
    </div>
  );
};
