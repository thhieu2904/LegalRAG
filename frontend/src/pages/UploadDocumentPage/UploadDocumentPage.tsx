/**
 * UploadDocumentPage
 * Standalone page for uploading documents to a collection
 */

import { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowLeft, Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { useDocumentStore } from '@/stores/useDocumentStore';
import { useAdminStore } from '@/stores/adminStore';
import styles from './UploadDocumentPage.module.css';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const UploadDocumentPage = () => {
  const { id: collectionId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const replaceDocumentId = searchParams.get('replace');

  const { uploadDocument, loading } = useDocumentStore();
  const { collections, fetchCollections } = useAdminStore();

  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Get current collection info
  const currentCollection = collections.find((c) => c.id === collectionId);

  // Fetch collections on mount
  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  const handleBack = () => {
    navigate(`/admin/collections/${collectionId}`);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile: File) => {
    // Validate file type
    if (selectedFile.type !== 'application/pdf') {
      setError('Chỉ chấp nhận file PDF');
      setFile(null);
      return;
    }

    // Validate file size
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`Kích thước file phải nhỏ hơn ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Auto-fill title from filename if empty
    if (!title) {
      const filename = selectedFile.name.replace(/\.pdf$/i, '');
      setTitle(filename);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!collectionId) {
      setError('Collection ID không hợp lệ');
      return;
    }

    if (!title.trim()) {
      setError('Vui lòng nhập tiêu đề tài liệu');
      return;
    }

    if (!file) {
      setError('Vui lòng chọn file PDF');
      return;
    }

    try {
      await uploadDocument(collectionId, title.trim(), file);
      setIsSuccess(true);

      // Navigate back after success
      setTimeout(() => {
        navigate(`/admin/collections/${collectionId}`);
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload thất bại');
    }
  };

  if (!collectionId) {
    return (
      <div className={styles.uploadPage}>
        <p className={styles.error}>Collection ID không hợp lệ</p>
      </div>
    );
  }

  return (
    <div className={styles.uploadPage}>
      {/* Back button */}
      <button onClick={handleBack} className={styles.backButton}>
        <ArrowLeft size={20} />
        Quay lại
      </button>

      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>
          {replaceDocumentId ? 'Thay thế tài liệu' : 'Thêm tài liệu mới'}
        </h1>
        {currentCollection && (
          <p className={styles.collectionInfo}>
            Bộ sưu tập: <strong>{currentCollection.display_name || currentCollection.name}</strong>
          </p>
        )}
      </div>

      {/* Upload Form */}
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Collection (read-only) */}
        <div className={styles.formGroup}>
          <label className={styles.label}>Bộ sưu tập</label>
          <input
            type="text"
            value={currentCollection?.display_name || currentCollection?.name || 'Loading...'}
            disabled
            className={styles.inputDisabled}
          />
        </div>

        {/* Title */}
        <div className={styles.formGroup}>
          <label className={styles.label}>
            Tiêu đề <span className={styles.required}>*</span>
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Nhập tiêu đề tài liệu..."
            className={styles.input}
            disabled={loading}
            required
          />
        </div>

        {/* File Upload */}
        <div className={styles.formGroup}>
          <label className={styles.label}>
            File PDF <span className={styles.required}>*</span>
          </label>
          <div
            className={`${styles.dropzone} ${isDragging ? styles.dropzoneDragging : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className={styles.fileInput}
              disabled={loading}
            />
            {file ? (
              <div className={styles.fileSelected}>
                <FileText size={48} className={styles.fileIcon} />
                <p className={styles.fileName}>{file.name}</p>
                <p className={styles.fileSize}>{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
              </div>
            ) : (
              <div className={styles.dropzoneEmpty}>
                <Upload size={48} className={styles.uploadIcon} />
                <p className={styles.dropzoneText}>Kéo thả file PDF vào đây hoặc nhấp để chọn</p>
                <p className={styles.dropzoneHint}>Tối đa 10MB</p>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className={styles.errorMessage}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Success Message */}
        {isSuccess && (
          <div className={styles.successMessage}>
            <CheckCircle size={20} />
            <span>Upload thành công! Đang chuyển hướng...</span>
          </div>
        )}

        {/* Actions */}
        <div className={styles.actions}>
          <button
            type="button"
            onClick={handleBack}
            className={styles.cancelButton}
            disabled={loading}
          >
            Hủy
          </button>
          <button type="submit" className={styles.submitButton} disabled={loading || isSuccess}>
            {loading ? (
              <>
                <div className={styles.spinner} />
                Đang upload...
              </>
            ) : (
              <>
                <Upload size={20} />
                {replaceDocumentId ? 'Thay thế' : 'Tải lên'}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
