/**
 * DocumentCard Component
 * Display individual document with icon, stats, and actions (styled like CollectionCard)
 */

import { Edit, Trash2, FileText, Database, File, Download } from 'lucide-react';
import { format } from 'date-fns';
import styles from './DocumentCard.module.css';
import type { Document } from '../../types/document.types';

interface DocumentCardProps {
  document: Document;
  onClick?: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onDownload?: (filePath: string, filename: string) => void;
}

// Format file size to human-readable format
const formatFileSize = (bytes: number | null): string => {
  if (!bytes) return 'N/A';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

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

export const DocumentCard = ({
  document,
  onClick,
  onEdit,
  onDelete,
  onDownload,
}: DocumentCardProps) => {
  const handleCardClick = () => {
    if (onClick) {
      onClick(document.id);
    }
  };

  const handleDownload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDownload && document.file_path) {
      onDownload(document.file_path, document.filename);
    }
  };

  return (
    <div
      className={styles.card}
      onClick={handleCardClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Header with Icon */}
      <div className={styles.header}>
        <div className={styles.iconContainer}>
          <FileText size={32} className={styles.icon} />
        </div>
        <div className={styles.actions}>
          {onDownload && document.file_path && (
            <button
              onClick={handleDownload}
              className={styles.actionButton}
              title="Tải xuống"
              aria-label="Download document"
            >
              <Download size={16} />
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(document.id);
            }}
            className={styles.actionButton}
            title="Chỉnh sửa"
            aria-label="Edit document"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(document.id);
            }}
            className={styles.actionButton}
            title="Xóa"
            aria-label="Delete document"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Document Info */}
      <div className={styles.info}>
        <h3 className={styles.name} title={document.title}>
          {document.title}
        </h3>
        <p className={styles.filename} title={document.filename}>
          {document.filename}
        </p>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.statItem}>
          <Database size={16} className={styles.statIcon} style={{ color: '#8b5cf6' }} />
          <span className={styles.statLabel}>Chunks</span>
          <span className={styles.statValue}>{document.chunk_count || 0}</span>
        </div>
        <div className={styles.statItem}>
          <FileText size={16} className={styles.statIcon} style={{ color: '#10b981' }} />
          <span className={styles.statLabel}>Forms</span>
          <span className={styles.statValue}>{document.forms_count || 0}</span>
        </div>
        <div className={styles.statItem}>
          <File size={16} className={styles.statIcon} style={{ color: '#3b82f6' }} />
          <span className={styles.statLabel}>Kích thước</span>
          <span className={styles.statValue}>{formatFileSize(document.file_size)}</span>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.date}>Tạo: {formatDate(document.created_at)}</span>
      </div>
    </div>
  );
};
