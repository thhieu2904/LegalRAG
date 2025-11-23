/**
 * FormCard Component
 * Display individual form with icon, stats, and actions (styled like DocumentCard)
 */

import { Trash2, FileText, Download } from 'lucide-react';
import { format } from 'date-fns';
import styles from './DocumentCard.module.css';
import type { Form } from '../../types/form.types';

interface FormCardProps {
  form: Form;
  onDelete: (id: string) => void;
  onDownload?: (filePath: string, filename: string) => void;
}

// Format date safely
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return 'N/A';
    }
    return format(date, 'dd/MM/yyyy HH:mm');
  } catch {
    return 'N/A';
  }
};

// Extract filename from path
const getFilename = (path: string | null): string => {
  if (!path) return 'form';
  const parts = path.split('/');
  return parts[parts.length - 1] || 'form';
};

export const FormCard = ({ form, onDelete, onDownload }: FormCardProps) => {
  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDownload && form.template_path) {
      const filename = getFilename(form.template_path);
      onDownload(form.template_path, filename);
    }
  };

  return (
    <div className={styles.card}>
      {/* Header with Icon */}
      <div className={styles.header}>
        <div className={styles.iconContainer}>
          <FileText size={32} className={styles.icon} />
        </div>
        <div className={styles.actions}>
          {onDownload && form.template_path && (
            <button
              onClick={handleDownload}
              className={styles.actionButton}
              title="Tải xuống"
              aria-label="Download form"
            >
              <Download size={16} />
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(form.id);
            }}
            className={styles.actionButton}
            title="Xóa"
            aria-label="Delete form"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Form Info */}
      <div className={styles.info}>
        <h3 className={styles.name} title={form.form_name}>
          {form.form_name}
        </h3>
        {form.form_code && (
          <p className={styles.filename} title={form.form_code}>
            {form.form_code}
          </p>
        )}
      </div>

      {/* Stats/Info */}
      <div className={styles.stats}>
        {form.form_type && (
          <div className={styles.statItem}>
            <FileText size={16} className={styles.statIcon} style={{ color: '#8b5cf6' }} />
            <span className={styles.statLabel}>Loại</span>
            <span className={styles.statValue}>{form.form_type}</span>
          </div>
        )}
        {form.description && (
          <div className={styles.statItem} style={{ gridColumn: '1 / -1' }}>
            <span className={styles.statLabel}>Mô tả</span>
            <span className={styles.statValue} style={{ fontSize: '0.8rem', opacity: 0.8 }}>
              {form.description.length > 80
                ? `${form.description.substring(0, 80)}...`
                : form.description}
            </span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.date}>Tạo: {formatDate(form.created_at)}</span>
      </div>
    </div>
  );
};
