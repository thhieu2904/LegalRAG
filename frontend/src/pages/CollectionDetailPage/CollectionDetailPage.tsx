/**
 * Collection Detail Page
 * Shows grid of document cards for a specific collection (similar to CollectionsPage)
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus } from 'lucide-react';
import { useDocumentStore } from '@/stores/useDocumentStore';
import { useAdminStore } from '@/stores/adminStore';
import { DocumentsGrid } from '@/components/admin/DocumentsGrid';
import { DeleteDocumentDialog } from '@/components/admin/DeleteDocumentDialog';
import styles from './CollectionDetailPage.module.css';

export const CollectionDetailPage = () => {
  const { id: collectionId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { documents, loading, fetchDocuments } = useDocumentStore();
  const { collections, fetchCollections } = useAdminStore();
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);

  // Get current collection info
  const currentCollection = collections.find((c) => c.id === collectionId);

  // Fetch collections and documents
  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  useEffect(() => {
    if (collectionId) {
      fetchDocuments(collectionId);
    }
  }, [collectionId, fetchDocuments]);

  const handleBack = () => {
    navigate('/admin/collections');
  };

  const handleAddDocument = () => {
    navigate(`/admin/collections/${collectionId}/upload`);
  };

  const handleClickDocument = (id: string) => {
    // Navigate to document detail page
    navigate(`/admin/documents/${id}`);
  };

  const handleEditDocument = (id: string) => {
    // Edit = Delete + Re-upload
    navigate(`/admin/collections/${collectionId}/upload?replace=${id}`);
  };

  const handleDeleteDocument = (id: string) => {
    setDeletingDocumentId(id);
  };

  const handleDownloadDocument = async (filePath: string, filename: string) => {
    try {
      const STORAGE_SERVICE_URL = 'http://localhost:8010';
      const url = `${STORAGE_SERVICE_URL}/download?file_path=${encodeURIComponent(filePath)}`;

      // Create a temporary link and click it
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Không thể tải xuống file. Vui lòng thử lại.');
    }
  };

  const handleDeleteConfirm = async () => {
    // Refresh after delete
    if (collectionId) {
      fetchDocuments(collectionId);
    }
  };

  const deletingDocument = documents.find((doc) => doc.id === deletingDocumentId);

  if (!collectionId) {
    return (
      <div className={styles.errorContainer}>
        <p>Collection ID not found</p>
      </div>
    );
  }

  return (
    <div className={styles.collectionDetailPage}>
      {/* Back button */}
      <button onClick={handleBack} className={styles.backButton}>
        <ArrowLeft size={20} />
        Quay lại danh sách collections
      </button>

      {/* Header */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{currentCollection?.display_name || 'Collection'}</h1>
          {currentCollection?.description && (
            <p className={styles.description}>{currentCollection.description}</p>
          )}
        </div>
        <button className={styles.addButton} onClick={handleAddDocument}>
          <Plus size={20} />
          Thêm tài liệu mới
        </button>
      </div>

      {/* Documents Grid */}
      <DocumentsGrid
        documents={documents}
        loading={loading}
        onClick={handleClickDocument}
        onEdit={handleEditDocument}
        onDelete={handleDeleteDocument}
        onCreate={handleAddDocument}
        onDownload={handleDownloadDocument}
      />

      {/* Delete Document Dialog */}
      <DeleteDocumentDialog
        isOpen={!!deletingDocumentId}
        documentId={deletingDocumentId}
        documentTitle={deletingDocument?.title || ''}
        onClose={() => setDeletingDocumentId(null)}
        onSuccess={handleDeleteConfirm}
      />
    </div>
  );
};
