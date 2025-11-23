/**
 * CollectionCard Component
 * Display individual collection with icon, stats, and actions
 */

import { Edit, Trash2, FileText, CheckCircle, Blocks } from 'lucide-react';
import * as Icons from 'lucide-react';
import { format } from 'date-fns';
import styles from './CollectionCard.module.css';
import type { CollectionCardProps } from './CollectionCard.types';

export const CollectionCard = ({
  id,
  name,
  slug,
  description,
  icon,
  color,
  document_count,
  total_chunks,
  is_active,
  created_at,
  onClick,
  onEdit,
  onDelete,
}: CollectionCardProps) => {
  // Get icon component from lucide-react
  const iconMap = Icons as unknown as Record<string, typeof Icons.FolderOpen>;
  const IconComponent = iconMap[icon] || Icons.FolderOpen;

  // Format date safely
  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return 'N/A';
      }
      return format(date, 'dd/MM/yyyy HH:mm');
    } catch {
      return 'N/A';
    }
  };

  return (
    <div
      className={styles.card}
      onClick={() => onClick?.(id)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Header with Icon */}
      <div className={styles.header}>
        <div className={styles.iconContainer} style={{ backgroundColor: `${color}15` }}>
          <IconComponent size={32} color={color} className={styles.icon} />
        </div>
        <div className={styles.actions}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(id);
            }}
            className={styles.actionButton}
            title="Chỉnh sửa"
            aria-label="Edit collection"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(id);
            }}
            className={styles.actionButton}
            title="Xóa"
            aria-label="Delete collection"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Collection Info */}
      <div className={styles.info}>
        <h3 className={styles.name}>{name}</h3>
        <p className={styles.slug}>{slug}</p>
        {description && <p className={styles.description}>{description}</p>}
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.statItem}>
          <FileText size={16} className={styles.statIcon} />
          <span className={styles.statLabel}>Văn bản</span>
          <span className={styles.statValue}>{document_count}</span>
        </div>
        <div className={styles.statItem}>
          <Blocks size={16} className={styles.statIcon} style={{ color: '#8b5cf6' }} />
          <span className={styles.statLabel}>Chunks</span>
          <span className={styles.statValue}>{total_chunks}</span>
        </div>
        <div className={styles.statItem}>
          <CheckCircle
            size={16}
            className={styles.statIcon}
            style={{ color: is_active ? '#10b981' : '#6b7280' }}
          />
          <span className={styles.statLabel}>Trạng thái</span>
          <span
            className={styles.statValue}
            style={{ color: is_active ? '#10b981' : '#6b7280', fontSize: '0.75rem' }}
          >
            {is_active ? 'Hoạt động' : 'Tạm dừng'}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.date}>Tạo: {formatDate(created_at)}</span>
      </div>
    </div>
  );
};
