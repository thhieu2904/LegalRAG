/**
 * EmptyState Component
 * Welcome screen for Legal RAG Q&A system
 */

import { Scale } from 'lucide-react';
import styles from './EmptyState.module.css';
import type { EmptyStateProps } from './EmptyState.types';

const quickTips = [
  {
    title: 'Hỏi về thủ tục hành chính',
    description:
      'Ví dụ: "Thủ tục đăng ký kết hôn cần những giấy tờ gì?" hoặc "Làm giấy khai sinh ở đâu?"',
  },
  {
    title: 'Hỏi tiếp để làm rõ',
    description:
      'Sau câu trả lời, bạn có thể hỏi thêm như "Lệ phí bao nhiêu?" hoặc "Thời gian xử lý mất bao lâu?" - hệ thống sẽ hiểu ngữ cảnh.',
  },
  {
    title: 'Xem nguồn văn bản',
    description:
      'Mỗi câu trả lời đều có trích dẫn từ văn bản pháp luật gốc. Bạn có thể kiểm tra độ tin cậy và tra cứu thêm.',
  },
];

export const EmptyState = ({ onSuggestionClick }: EmptyStateProps) => {
  void onSuggestionClick;
  return (
    <div className={styles.emptyState}>
      <div className={styles.content}>
        <div className={styles.hero}>
          <div className={styles.iconWrapper}>
            <Scale size={48} />
          </div>
          <div className={styles.heroText}>
            <h2 className={styles.title}>Hỏi đáp Pháp luật</h2>
            <p className={styles.description}>
              Đặt câu hỏi về thủ tục hành chính, quy định pháp luật. Hệ thống sẽ tìm kiếm trong kho
              văn bản pháp luật và trả lời dựa trên nguồn chính thống.
            </p>
          </div>
        </div>

        <div className={styles.quickTips}>
          {quickTips.map((tip) => (
            <div key={tip.title} className={styles.quickTip}>
              <h3 className={styles.quickTipTitle}>{tip.title}</h3>
              <p className={styles.quickTipDescription}>{tip.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
