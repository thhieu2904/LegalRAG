/**
 * UploadFormModal Component
 * Modal for uploading form files with metadata
 */

import { useState } from 'react';
import { X, Upload, FileText } from 'lucide-react';
import styles from './UploadFormModal.module.css';

const ADMIN_SERVICE_URL = 'http://localhost:8001';

interface UploadFormModalProps {
  isOpen: boolean;
  documentId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const UploadFormModal = ({
  isOpen,
  documentId,
  onClose,
  onSuccess,
}: UploadFormModalProps) => {
  const [formName, setFormName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];

      if (!allowedTypes.includes(selectedFile.type)) {
        setError('Chỉ hỗ trợ file PDF, DOC, DOCX');
        return;
      }

      setFile(selectedFile);
      setError(null);

      // Auto-fill form name from filename if empty
      if (!formName) {
        const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '');
        setFormName(nameWithoutExt);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!file) {
      setError('Vui lòng chọn file biểu mẫu');
      return;
    }

    if (!formName.trim()) {
      setError('Vui lòng nhập tên biểu mẫu');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('document_id', documentId);
      formData.append('form_name', formName.trim());

      if (description.trim()) {
        formData.append('description', description.trim());
      }

      const response = await fetch(`${ADMIN_SERVICE_URL}/admin/forms`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to upload form');
      }

      // Reset form and close modal
      setFormName('');
      setDescription('');
      setFile(null);
      onSuccess();
    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Lỗi khi tải lên biểu mẫu');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    if (!uploading) {
      setFormName('');
      setDescription('');
      setFile(null);
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
          <h2 className={styles.modalTitle}>
            <Upload size={24} />
            Thêm biểu mẫu mới
          </h2>
          <button
            onClick={handleClose}
            className={styles.closeButton}
            disabled={uploading}
            aria-label="Close modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          {/* File Upload */}
          <div className={styles.formGroup}>
            <label htmlFor="file-upload" className={styles.label}>
              File biểu mẫu <span className={styles.required}>*</span>
            </label>
            <div className={styles.fileInputWrapper}>
              <input
                id="file-upload"
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.doc,.docx"
                disabled={uploading}
                className={styles.fileInput}
              />
              <div className={styles.fileInputLabel}>
                <FileText size={20} />
                <span>{file ? file.name : 'Chọn file biểu mẫu...'}</span>
              </div>
            </div>
            <p className={styles.hint}>Chỉ hỗ trợ: PDF, DOC, DOCX</p>
          </div>

          {/* Form Name */}
          <div className={styles.formGroup}>
            <label htmlFor="form-name" className={styles.label}>
              Tên biểu mẫu <span className={styles.required}>*</span>
            </label>
            <input
              id="form-name"
              type="text"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              placeholder="Ví dụ: Đơn đề nghị cấp giấy khai sinh"
              disabled={uploading}
              className={styles.input}
              required
            />
          </div>

          {/* Description */}
          <div className={styles.formGroup}>
            <label htmlFor="description" className={styles.label}>
              Mô tả
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Mô tả ngắn gọn về biểu mẫu..."
              disabled={uploading}
              className={styles.textarea}
              rows={3}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div className={styles.error}>
              <p>{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className={styles.modalActions}>
            <button
              type="button"
              onClick={handleClose}
              disabled={uploading}
              className={styles.cancelButton}
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={uploading || !file || !formName.trim()}
              className={styles.submitButton}
            >
              {uploading ? (
                <>
                  <div className={styles.spinner} />
                  Đang tải lên...
                </>
              ) : (
                <>
                  <Upload size={16} />
                  Tải lên
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
