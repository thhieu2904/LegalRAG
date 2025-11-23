/**
 * DeleteFormDialog Component
 * Confirmation dialog for deleting forms
 */

import { useState } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import styles from './DeleteFormDialog.module.css';

const ADMIN_SERVICE_URL = 'http://localhost:8001';

interface DeleteFormDialogProps {
  isOpen: boolean;
  formId: string | null;
  formName: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const DeleteFormDialog = ({
  isOpen,
  formId,
  formName,
  onClose,
  onSuccess,
}: DeleteFormDialogProps) => {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!formId) return;

    try {
      setDeleting(true);
      setError(null);

      const response = await fetch(`${ADMIN_SERVICE_URL}/admin/forms/${formId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete form');
      }

      onSuccess();
      onClose();
    } catch (err) {
      console.error('Delete error:', err);
      setError(err instanceof Error ? err.message : 'Lỗi khi xóa biểu mẫu');
    } finally {
      setDeleting(false);
    }
  };

  const handleClose = () => {
    if (!deleting) {
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={handleClose}>
      <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.warningIcon}>
            <AlertTriangle size={24} />
          </div>
          <h2 className={styles.modalTitle}>Xác nhận xóa biểu mẫu</h2>
          <button
            onClick={handleClose}
            className={styles.closeButton}
            disabled={deleting}
            aria-label="Close dialog"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.modalBody}>
          <p className={styles.message}>Bạn có chắc chắn muốn xóa biểu mẫu này?</p>
          <div className={styles.itemInfo}>
            <strong>Tên biểu mẫu:</strong> {formName}
          </div>
          <p className={styles.warning}>
            ⚠️ Hành động này không thể hoàn tác. File biểu mẫu sẽ bị xóa vĩnh viễn khỏi hệ thống.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className={styles.error}>
            <p>{error}</p>
          </div>
        )}

        {/* Actions */}
        <div className={styles.modalActions}>
          <button onClick={handleClose} disabled={deleting} className={styles.cancelButton}>
            Hủy
          </button>
          <button onClick={handleDelete} disabled={deleting} className={styles.deleteButton}>
            {deleting ? (
              <>
                <div className={styles.spinner} />
                Đang xóa...
              </>
            ) : (
              'Xóa biểu mẫu'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
