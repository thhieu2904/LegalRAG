/**
 * UploadStep Component
 * Step 1: Upload DOCX file for template creation
 */

import { useState } from 'react';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import styles from './CreateTemplateModal.module.css';

interface UploadStepProps {
  documentId: string;
  onUpload: (file: File, formName: string, description: string) => void;
  uploading: boolean;
  error: string | null;
}

export const UploadStep = ({ onUpload, uploading, error }: Omit<UploadStepProps, 'documentId'>) => {
  const [file, setFile] = useState<File | null>(null);
  const [formName, setFormName] = useState('');
  const [description, setDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (selectedFile: File | null) => {
    if (!selectedFile) return;

    // Validate file type
    if (!selectedFile.name.endsWith('.docx')) {
      alert('Chỉ hỗ trợ file DOCX');
      return;
    }

    setFile(selectedFile);

    // Auto-fill form name from filename
    if (!formName) {
      const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '');
      setFormName(nameWithoutExt);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    handleFileChange(selectedFile || null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files?.[0];
    handleFileChange(droppedFile || null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (file && formName.trim()) {
      onUpload(file, formName.trim(), description.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.stepForm}>
      <div className={styles.stepContent}>
        <h3 className={styles.stepTitle}>Bước 1: Tải lên file mẫu</h3>
        <p className={styles.stepDescription}>
          Hệ thống sẽ tự động phát hiện các vị trí có thể điền trong file DOCX của bạn
        </p>

        {/* File Upload Dropzone */}
        <div
          className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ''} ${
            file ? styles.dropzoneHasFile : ''
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            id="file-upload"
            type="file"
            onChange={handleInputChange}
            accept=".docx"
            disabled={uploading}
            className={styles.fileInput}
          />

          <label htmlFor="file-upload" className={styles.dropzoneLabel}>
            {file ? (
              <>
                <FileText size={48} className={styles.fileIcon} />
                <p className={styles.fileName}>{file.name}</p>
                <p className={styles.fileSize}>{(file.size / 1024).toFixed(2)} KB</p>
                <p className={styles.changeFile}>Click để thay đổi file</p>
              </>
            ) : (
              <>
                <Upload size={48} className={styles.uploadIcon} />
                <p className={styles.dropzoneText}>Kéo thả file DOCX vào đây hoặc click để chọn</p>
                <p className={styles.dropzoneHint}>Chỉ hỗ trợ file .docx</p>
              </>
            )}
          </label>
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
            Mô tả (tùy chọn)
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
          <div className={styles.errorBox}>
            <AlertCircle size={20} />
            <p>{error}</p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className={styles.stepActions}>
        <div className={styles.stepInfo}>Bước 1/3</div>
        <button
          type="submit"
          disabled={uploading || !file || !formName.trim()}
          className={styles.nextButton}
        >
          {uploading ? (
            <>
              <div className={styles.spinner} />
              Đang phát hiện...
            </>
          ) : (
            'Tiếp theo →'
          )}
        </button>
      </div>
    </form>
  );
};
