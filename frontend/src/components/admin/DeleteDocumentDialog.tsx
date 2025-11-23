import { useState } from 'react';
import { X, AlertTriangle, AlertCircle } from 'lucide-react';
import { useDocumentStore } from '../../stores/useDocumentStore';
import styles from './DeleteDocumentDialog.module.css';

interface DeleteDocumentDialogProps {
  isOpen: boolean;
  documentId: string | null;
  documentTitle: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const DeleteDocumentDialog = ({
  isOpen,
  documentId,
  documentTitle,
  onClose,
  onSuccess,
}: DeleteDocumentDialogProps) => {
  const { deleteDocument, loading } = useDocumentStore();
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!documentId) {
      setError('Document ID is missing');
      return;
    }

    setError(null);
    try {
      await deleteDocument(documentId);
      onClose();
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  if (!isOpen || !documentId) return null;

  return (
    <div className={styles.overlay}>
      <div className={styles.dialog}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.headerContent}>
            <div className={styles.iconWrapper}>
              <AlertTriangle />
            </div>
            <h2 className={styles.title}>Delete Document</h2>
          </div>
          <button onClick={handleClose} disabled={loading} className={styles.closeButton}>
            <X />
          </button>
        </div>

        {/* Body */}
        <div className={styles.body}>
          {/* Error Message */}
          {error && (
            <div className={styles.errorAlert}>
              <AlertCircle />
              <div className={styles.errorContent}>
                <p className={styles.errorTitle}>Error</p>
                <p className={styles.errorMessage}>{error}</p>
              </div>
            </div>
          )}

          {/* Warning Message */}
          <div className={styles.warningAlert}>
            <p>Are you sure you want to permanently delete this document?</p>
            <p className={styles.documentTitle}>"{documentTitle}"</p>
          </div>

          {/* Consequences */}
          <div className={styles.consequencesAlert}>
            <p className={styles.consequencesTitle}>This action will:</p>
            <ul className={styles.consequencesList}>
              <li>Permanently delete the document</li>
              <li>Remove all associated chunks</li>
              <li>Remove all extracted forms</li>
              <li>Cannot be undone</li>
            </ul>
          </div>

          {/* Actions */}
          <div className={styles.actions}>
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className={styles.cancelButton}
            >
              Cancel
            </button>
            <button onClick={handleDelete} disabled={loading} className={styles.deleteButton}>
              {loading ? (
                <>
                  <div className={styles.spinner}></div>
                  Deleting...
                </>
              ) : (
                'Delete Permanently'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
