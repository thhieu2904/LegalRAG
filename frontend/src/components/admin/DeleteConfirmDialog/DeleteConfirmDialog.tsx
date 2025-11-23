/**
 * DeleteConfirmDialog Component
 * Confirmation dialog for deleting collection with CASCADE warning
 */

import { useState, useEffect, type ChangeEvent } from 'react';
import { X, AlertTriangle, Trash2, Loader2 } from 'lucide-react';
import type { DeleteConfirmDialogProps } from './DeleteConfirmDialog.types';
import styles from './DeleteConfirmDialog.module.css';

export const DeleteConfirmDialog = ({
  isOpen,
  collection,
  onClose,
  onConfirm,
}: DeleteConfirmDialogProps) => {
  const [confirmText, setConfirmText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset state when dialog opens/closes
  useEffect(() => {
    if (isOpen) {
      setConfirmText('');
      setIsDeleting(false);
      setError(null);
    }
  }, [isOpen]);

  const handleConfirmTextChange = (e: ChangeEvent<HTMLInputElement>) => {
    setConfirmText(e.target.value);
    if (error) setError(null);
  };

  const handleDelete = async () => {
    if (!collection) return;

    // Validate confirmation text
    if (confirmText !== collection.display_name) {
      setError('Tên bộ sưu tập không khớp. Vui lòng nhập chính xác.');
      return;
    }

    setIsDeleting(true);
    setError(null);

    try {
      await onConfirm(collection.id);
      onClose();
    } catch (err) {
      console.error('Failed to delete collection:', err);
      setError('Xóa bộ sưu tập thất bại. Vui lòng thử lại.');
    } finally {
      setIsDeleting(false);
    }
  };

  // Close handlers
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isDeleting) {
      onClose();
    }
  };

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isDeleting) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, isDeleting, onClose]);

  if (!isOpen || !collection) return null;

  const isConfirmValid = confirmText === collection.display_name;

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.dialog}>
        {/* Header */}
        <div className={styles.header}>
          <div className={styles.iconWrapper}>
            <AlertTriangle size={24} className={styles.warningIcon} />
          </div>
          <h2 className={styles.title}>Xác nhận xóa bộ sưu tập</h2>
          <button
            type="button"
            onClick={onClose}
            className={styles.closeButton}
            disabled={isDeleting}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* Collection Info */}
          <div className={styles.collectionInfo}>
            <div
              className={styles.collectionIcon}
              style={{
                backgroundColor: `${collection.color}15`,
                color: collection.color,
              }}
            >
              <Trash2 size={24} />
            </div>
            <div className={styles.collectionDetails}>
              <h3 className={styles.collectionName}>{collection.display_name}</h3>
              <p className={styles.collectionSlug}>slug: {collection.name}</p>
            </div>
          </div>

          {/* Warning Messages */}
          <div className={styles.warningBox}>
            <AlertTriangle size={18} className={styles.warningBoxIcon} />
            <div className={styles.warningContent}>
              <p className={styles.warningTitle}>⚠️ CẢNH BÁO: HÀNH ĐỘNG KHÔNG THỂ HOÀN TÁC</p>
              <ul className={styles.warningList}>
                <li>
                  Xóa bộ sưu tập này sẽ <strong>XÓA VĨNH VIỄN</strong>:
                </li>
                <li>
                  ✗ <strong>{collection.document_count} tài liệu</strong> trong bộ sưu tập
                </li>
                <li>
                  ✗ <strong>{collection.total_chunks} chunks</strong> (embeddings)
                </li>
                <li>✗ Tất cả biểu mẫu liên quan (forms)</li>
                <li>✗ Lịch sử tìm kiếm và logs</li>
              </ul>
              <p className={styles.warningFooter}>
                Dữ liệu sẽ bị xóa khỏi cơ sở dữ liệu và không thể khôi phục.
              </p>
            </div>
          </div>

          {/* Confirmation Input */}
          <div className={styles.confirmSection}>
            <label htmlFor="confirm-text" className={styles.confirmLabel}>
              Để xác nhận, vui lòng nhập tên bộ sưu tập:
            </label>
            <code className={styles.confirmTarget}>{collection.display_name}</code>
            <input
              id="confirm-text"
              type="text"
              value={confirmText}
              onChange={handleConfirmTextChange}
              placeholder="Nhập tên bộ sưu tập..."
              className={`${styles.confirmInput} ${error ? styles.confirmInputError : ''}`}
              disabled={isDeleting}
              autoComplete="off"
            />
            {error && (
              <div className={styles.errorMessage}>
                <AlertTriangle size={14} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          <button
            type="button"
            onClick={onClose}
            className={styles.cancelButton}
            disabled={isDeleting}
          >
            Hủy
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className={styles.deleteButton}
            disabled={!isConfirmValid || isDeleting}
          >
            {isDeleting ? (
              <>
                <Loader2 size={18} className={styles.spinner} />
                Đang xóa...
              </>
            ) : (
              <>
                <Trash2 size={18} />
                Xóa vĩnh viễn
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
