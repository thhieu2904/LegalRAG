/**
 * Collections Management Page
 * CRUD interface for managing document collections
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { useAdminStore } from '@/stores/adminStore';
import { CollectionsGrid } from '@/components/admin/CollectionsGrid';
import { CreateCollectionModal } from '@/components/admin/CreateCollectionModal';
import { EditCollectionModal } from '@/components/admin/EditCollectionModal';
import { DeleteConfirmDialog } from '@/components/admin/DeleteConfirmDialog';
import type { Collection } from '@/types/admin.types';
import styles from './CollectionsPage.module.css';

export const CollectionsPage = () => {
  const navigate = useNavigate();
  const { collections, loading, fetchCollections, removeCollection } = useAdminStore();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null);
  const [deletingCollection, setDeletingCollection] = useState<Collection | null>(null);

  // Fetch collections on mount
  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  const handleCreate = () => {
    setIsCreateModalOpen(true);
  };

  const handleCreateSuccess = () => {
    // Refresh collections list after creating
    fetchCollections();
  };

  const handleEdit = (id: string) => {
    const collection = collections.find((c) => c.id === id);
    if (collection) {
      setEditingCollection(collection);
    }
  };

  const handleEditSuccess = () => {
    // Refresh collections list after editing
    fetchCollections();
  };

  const handleDelete = (id: string) => {
    const collection = collections.find((c) => c.id === id);
    if (collection) {
      setDeletingCollection(collection);
    }
  };

  const handleDeleteConfirm = async (id: string) => {
    await removeCollection(id);
    // Refresh collections list after deleting
    fetchCollections();
  };

  const handleCollectionClick = (id: string) => {
    navigate(`/admin/collections/${id}`);
  };

  return (
    <div className={styles.collectionsPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>Quản lý Bộ sưu tập</h1>
        <button className={styles.createButton} onClick={handleCreate}>
          <Plus size={20} />
          Tạo bộ sưu tập mới
        </button>
      </div>

      <CollectionsGrid
        collections={collections}
        loading={loading}
        onCollectionClick={handleCollectionClick}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onCreate={handleCreate}
      />

      {/* Create Collection Modal */}
      <CreateCollectionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* Edit Collection Modal */}
      <EditCollectionModal
        isOpen={!!editingCollection}
        collection={editingCollection}
        onClose={() => setEditingCollection(null)}
        onSuccess={handleEditSuccess}
      />

      {/* Delete Confirm Dialog */}
      <DeleteConfirmDialog
        isOpen={!!deletingCollection}
        collection={deletingCollection}
        onClose={() => setDeletingCollection(null)}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
};
