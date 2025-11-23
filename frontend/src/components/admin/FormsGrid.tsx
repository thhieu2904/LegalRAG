/**
 * FormsGrid Component
 * Display grid of form cards (styled like DocumentsGrid)
 */

import { Plus, FileText } from 'lucide-react';
import { FormCard } from './FormCard';
import styles from './DocumentsGrid.module.css';
import type { Form } from '../../types/form.types';

interface FormsGridProps {
  forms: Form[];
  loading?: boolean;
  onDelete: (id: string) => void;
  onDownload?: (filePath: string, filename: string) => void;
  onCreate: () => void;
}

export const FormsGrid = ({
  forms,
  loading = false,
  onDelete,
  onDownload,
  onCreate,
}: FormsGridProps) => {
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p>Đang tải biểu mẫu...</p>
      </div>
    );
  }

  if (forms.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <FileText size={64} className={styles.emptyIcon} />
        <h3 className={styles.emptyTitle}>Chưa có biểu mẫu nào</h3>
        <p className={styles.emptyDescription}>Thêm biểu mẫu đầu tiên cho tài liệu này</p>
        <button onClick={onCreate} className={styles.emptyButton}>
          <Plus size={20} />
          Thêm biểu mẫu
        </button>
      </div>
    );
  }

  return (
    <div className={styles.grid}>
      {forms.map((form) => (
        <FormCard key={form.id} form={form} onDelete={onDelete} onDownload={onDownload} />
      ))}
    </div>
  );
};
