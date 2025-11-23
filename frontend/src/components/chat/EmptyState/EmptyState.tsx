/**
 * EmptyState Component
 */

import { MessageSquare } from 'lucide-react';
import styles from './EmptyState.module.css';
import type { EmptyStateProps } from './EmptyState.types';

const quickTips = [
  {
    title: 'Nhắc đến môn học',
    description:
      'Ghi rõ tên môn hoặc chủ đề của tài liệu (ví dụ: "Cấu trúc dữ liệu" hay "Lập trình Java") để hệ thống tra cứu nhanh hơn.',
  },
  {
    title: 'Nói rõ mong muốn',
    description:
      'Cho biết bạn cần tóm tắt, định nghĩa hay ví dụ thực hành để nhận được câu trả lời sát nhu cầu.',
  },
  {
    title: 'Theo dõi nguồn tham khảo',
    description:
      'Sau mỗi câu trả lời, mở mục "Nguồn tham khảo" để xem tài liệu gốc và trích dẫn liên quan.',
  },
];

export const EmptyState = ({ onSuggestionClick }: EmptyStateProps) => {
  void onSuggestionClick;
  return (
    <div className={styles.emptyState}>
      <div className={styles.content}>
        <div className={styles.hero}>
          <div className={styles.iconWrapper}>
            <MessageSquare size={48} />
          </div>
          <div className={styles.heroText}>
            <h2 className={styles.title}>Bắt đầu cuộc trò chuyện</h2>
            <p className={styles.description}>
              Đặt câu hỏi về tài liệu học tập mà bạn quan tâm. AI sẽ tìm kiếm trong kho dữ liệu đã
              được khoa xác thực và gửi lại câu trả lời phù hợp.
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
