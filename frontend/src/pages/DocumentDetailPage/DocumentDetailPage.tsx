/**
 * Document Detail Page
 * Shows document details, chunks list, and forms list with CRUD operations
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Database } from 'lucide-react';
import { FormsGrid } from '@/components/admin/FormsGrid';
import { UploadFormModal } from '@/components/admin/UploadFormModal';
import { DeleteFormDialog } from '@/components/admin/DeleteFormDialog';
import styles from './DocumentDetailPage.module.css';
import type { Document } from '@/types/document.types';
import type { Form } from '@/types/form.types';

const ADMIN_SERVICE_URL = 'http://localhost:8001';
const STORAGE_SERVICE_URL = 'http://localhost:8010';

export const DocumentDetailPage = () => {
  const { id: documentId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [document, setDocument] = useState<Document | null>(null);
  const [forms, setForms] = useState<Form[]>([]);
  const [loading, setLoading] = useState(true);
  const [formsLoading, setFormsLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [deletingFormId, setDeletingFormId] = useState<string | null>(null);

  // Fetch document details
  useEffect(() => {
    if (!documentId) return;

    const fetchDocument = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${ADMIN_SERVICE_URL}/admin/documents?limit=1000`);
        if (!response.ok) throw new Error('Failed to fetch document');

        const data = await response.json();
        const doc = data.documents?.find((d: Document) => d.id === documentId);

        if (doc) {
          setDocument(doc);
        } else {
          console.error('Document not found');
        }
      } catch (error) {
        console.error('Error fetching document:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  // Fetch forms for document
  useEffect(() => {
    const fetchForms = async () => {
      if (!documentId) return;

      try {
        setFormsLoading(true);
        const response = await fetch(`${ADMIN_SERVICE_URL}/admin/documents/${documentId}/forms`);
        if (!response.ok) throw new Error('Failed to fetch forms');

        const data = await response.json();
        setForms(data.forms || []);
      } catch (error) {
        console.error('Error fetching forms:', error);
        setForms([]);
      } finally {
        setFormsLoading(false);
      }
    };

    fetchForms();
  }, [documentId]);

  const fetchForms = async () => {
    if (!documentId) return;

    try {
      setFormsLoading(true);
      const response = await fetch(`${ADMIN_SERVICE_URL}/admin/documents/${documentId}/forms`);
      if (!response.ok) throw new Error('Failed to fetch forms');

      const data = await response.json();
      setForms(data.forms || []);
    } catch (error) {
      console.error('Error fetching forms:', error);
      setForms([]);
    } finally {
      setFormsLoading(false);
    }
  };

  const handleBack = () => {
    if (document?.collection_id) {
      navigate(`/admin/collections/${document.collection_id}`);
    } else {
      navigate('/admin/collections');
    }
  };

  const handleDownloadDocument = async () => {
    if (!document?.file_path) return;

    try {
      const url = `${STORAGE_SERVICE_URL}/download?file_path=${encodeURIComponent(document.file_path)}`;
      const link = window.document.createElement('a');
      link.href = url;
      link.download = document.filename;
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Không thể tải xuống file. Vui lòng thử lại.');
    }
  };

  const handleDownloadForm = async (filePath: string, filename: string) => {
    try {
      const url = `${STORAGE_SERVICE_URL}/download?file_path=${encodeURIComponent(filePath)}`;
      const link = window.document.createElement('a');
      link.href = url;
      link.download = filename;
      window.document.body.appendChild(link);
      link.click();
      window.document.body.removeChild(link);
    } catch (error) {
      console.error('Download failed:', error);
      alert('Không thể tải xuống file. Vui lòng thử lại.');
    }
  };

  const handleDeleteForm = (formId: string) => {
    setDeletingFormId(formId);
  };

  const handleDeleteSuccess = () => {
    fetchForms();
    setDeletingFormId(null);
  };

  const handleUploadSuccess = () => {
    fetchForms();
    setShowUploadModal(false);
  };

  const deletingForm = forms.find((f) => f.id === deletingFormId);

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <p>Đang tải tài liệu...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className={styles.errorContainer}>
        <p>Không tìm thấy tài liệu</p>
        <button onClick={handleBack} className={styles.backButton}>
          Quay lại
        </button>
      </div>
    );
  }

  return (
    <div className={styles.documentDetailPage}>
      {/* Back button */}
      <button onClick={handleBack} className={styles.backButton}>
        <ArrowLeft size={20} />
        Quay lại danh sách tài liệu
      </button>

      {/* Document Header */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>{document.title}</h1>
          <p className={styles.filename}>{document.filename}</p>
          <div className={styles.stats}>
            <span className={styles.statItem}>
              <Database size={16} />
              {document.chunk_count || 0} chunks
            </span>
            <span className={styles.statItem}>{document.forms_count || 0} biểu mẫu</span>
          </div>
        </div>
        <button onClick={handleDownloadDocument} className={styles.downloadButton}>
          Tải xuống tài liệu
        </button>
      </div>

      {/* Chunks Section */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>
            <Database size={24} />
            Chunks ({document.chunk_count || 0})
          </h2>
        </div>
        <div className={styles.chunksInfo}>
          <p>
            Tài liệu đã được chia thành {document.chunk_count || 0} chunks để tìm kiếm semantics.
          </p>
        </div>
      </section>

      {/* Forms Section */}
      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Biểu mẫu ({forms.length})</h2>
          <button onClick={() => setShowUploadModal(true)} className={styles.addButton}>
            <Plus size={20} />
            Thêm biểu mẫu
          </button>
        </div>
        <FormsGrid
          forms={forms}
          loading={formsLoading}
          onDelete={handleDeleteForm}
          onDownload={handleDownloadForm}
          onCreate={() => setShowUploadModal(true)}
        />
      </section>

      {/* Upload Form Modal */}
      <UploadFormModal
        isOpen={showUploadModal}
        documentId={documentId!}
        onClose={() => setShowUploadModal(false)}
        onSuccess={handleUploadSuccess}
      />

      {/* Delete Form Dialog */}
      <DeleteFormDialog
        isOpen={!!deletingFormId}
        formId={deletingFormId}
        formName={deletingForm?.form_name || ''}
        onClose={() => setDeletingFormId(null)}
        onSuccess={handleDeleteSuccess}
      />
    </div>
  );
};
