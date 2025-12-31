/**
 * CollectionsGrid Component
 * Grid layout for displaying collections with loading and empty states
 */

import { Loader2, FolderOpen, Plus } from 'lucide-react';
import { CollectionCard } from '../CollectionCard';
import type { Collection } from '@/types/admin.types';
import styles from './CollectionsGrid.module.css';

export interface CollectionsGridProps {
  collections: Collection[];
  loading: boolean;
  onCollectionClick?: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  onCreate: () => void;
}

export const CollectionsGrid = ({
  collections,
  loading,
  onCollectionClick,
  onEdit,
  onDelete,
  onCreate,
}: CollectionsGridProps) => {
  // Loading state
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Loader2 size={48} className={styles.spinner} />
        <p className={styles.loadingText}>Đang tải danh sách collections...</p>
      </div>
    );
  }

  // Empty state
  if (collections.length === 0) {
    return (
      <div className={styles.emptyContainer}>
        <div className={styles.emptyIcon}>
          <FolderOpen size={64} strokeWidth={1.5} />
        </div>
        <h3 className={styles.emptyTitle}>Chưa có bộ sưu tập nào</h3>
        <p className={styles.emptyDescription}>
          Tạo bộ sưu tập đầu tiên để bắt đầu quản lý tài liệu pháp luật
        </p>
        <button onClick={onCreate} className={styles.emptyButton}>
          <Plus size={20} />
          Tạo bộ sưu tập đầu tiên
        </button>
      </div>
    );
  }

  // Grid display
  return (
    <div className={styles.grid}>
      {collections.map((collection) => (
        <CollectionCard
          key={collection.id}
          id={collection.id}
          name={collection.display_name}
          slug={collection.name}
          description={collection.description || undefined}
          icon={collection.icon}
          color={collection.color}
          document_count={collection.document_count}
          total_chunks={collection.total_chunks}
          is_active={collection.is_active}
          created_at={collection.created_at}
          onClick={onCollectionClick}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
};
