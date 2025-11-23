/**
 * DocumentsPage (Global view of all documents)
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { DocumentsGrid } from '@/components/admin/DocumentsGrid';
import { DeleteDocumentDialog } from '@/components/admin/DeleteDocumentDialog';
import { useDocumentStore } from '@/stores/useDocumentStore';

export const DocumentsPage = () => {
  const navigate = useNavigate();
  const { documents, loading, fetchDocuments } = useDocumentStore();
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);

  useEffect(() => {
    // Fetch all documents (no collection filter)
    fetchDocuments();
  }, [fetchDocuments]);

  const handleEdit = (id: string) => {
    const doc = documents.find((d) => d.id === id);
    if (doc?.collection_id) {
      navigate(`/admin/collections/${doc.collection_id}/upload?replace=${id}`);
    }
  };

  const handleDelete = (id: string) => {
    setDeletingDocumentId(id);
  };

  const handleDeleteSuccess = () => {
    // Refresh documents list
    fetchDocuments();
  };

  const handleCreate = () => {
    // Redirect to collections page (need to select collection first)
    navigate('/admin/collections');
  };

  const deletingDocument = documents.find((doc) => doc.id === deletingDocumentId);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Quản lý Tài liệu</h1>
            <p className="text-gray-600 mt-2">Xem tất cả tài liệu trong hệ thống</p>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <Plus size={20} />
            Thêm tài liệu
          </button>
        </div>

        {/* Documents Grid */}
        <DocumentsGrid
          documents={documents}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onCreate={handleCreate}
        />

        {/* Delete Document Dialog */}
        <DeleteDocumentDialog
          isOpen={!!deletingDocumentId}
          documentId={deletingDocumentId}
          documentTitle={deletingDocument?.title || ''}
          onClose={() => setDeletingDocumentId(null)}
          onSuccess={handleDeleteSuccess}
        />
      </div>
    </div>
  );
};
