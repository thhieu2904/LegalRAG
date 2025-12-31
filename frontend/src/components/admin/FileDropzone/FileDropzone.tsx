/**
 * FileDropzone Component
 * Drag & drop file upload with validation
 */

import { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import styles from './FileDropzone.module.css';
import { Button } from '@/components/common/Button';

interface FileDropzoneProps {
  /** Accepted file types (e.g., '.pdf,.docx,.txt') */
  accept?: string;
  /** Maximum file size in bytes (default: 10MB) */
  maxSize?: number;
  /** Selected file */
  file: File | null;
  /** File selection callback */
  onFileSelect: (file: File | null) => void;
  /** Error callback */
  onError?: (error: string) => void;
  /** Disabled state */
  disabled?: boolean;
}

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10MB
const DEFAULT_ACCEPT = '.pdf,.docx,.txt';

export function FileDropzone({
  accept = DEFAULT_ACCEPT,
  maxSize = DEFAULT_MAX_SIZE,
  file,
  onFileSelect,
  onError,
  disabled = false,
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * Validate file
   */
  const validateFile = (file: File): string | null => {
    // Check size
    if (file.size > maxSize) {
      const sizeMB = (maxSize / (1024 * 1024)).toFixed(0);
      return `File quá lớn. Tối đa ${sizeMB}MB`;
    }

    // Check type
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    const acceptedTypes = accept.split(',').map((t) => t.trim().toLowerCase());

    if (!acceptedTypes.includes(extension)) {
      return `Định dạng không hợp lệ. Chỉ chấp nhận: ${accept}`;
    }

    return null;
  };

  /**
   * Handle file selection
   */
  const handleFile = (selectedFile: File) => {
    const error = validateFile(selectedFile);
    if (error) {
      onError?.(error);
      return;
    }

    onFileSelect(selectedFile);
  };

  /**
   * Handle drag events
   */
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0]) {
      handleFile(files[0]);
    }
  };

  /**
   * Handle input change
   */
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0 && files[0]) {
      handleFile(files[0]);
    }
  };

  /**
   * Open file browser
   */
  const handleBrowseClick = () => {
    inputRef.current?.click();
  };

  /**
   * Clear selected file
   */
  const handleClear = () => {
    onFileSelect(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  /**
   * Format file size
   */
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className={styles.dropzone}>
      {/* Dropzone area */}
      <div
        className={`${styles.dropArea} ${isDragging ? styles.dragging : ''} ${
          disabled ? styles.disabled : ''
        } ${file ? styles.hasFile : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!file && !disabled ? handleBrowseClick : undefined}
      >
        {file ? (
          /* File selected */
          <div className={styles.filePreview}>
            <div className={styles.fileIcon}>📄</div>
            <div className={styles.fileInfo}>
              <div className={styles.fileName}>{file.name}</div>
              <div className={styles.fileSize}>{formatFileSize(file.size)}</div>
            </div>
            {!disabled && (
              <Button variant="ghost" size="sm" onClick={handleClear}>
                ✕
              </Button>
            )}
          </div>
        ) : (
          /* Empty state */
          <div className={styles.emptyState}>
            <div className={styles.uploadIcon}>📁</div>
            <div className={styles.uploadText}>
              <strong>Kéo thả file vào đây</strong>
              <span>hoặc click để chọn</span>
            </div>
            <div className={styles.uploadHint}>
              {accept} • Tối đa {(maxSize / (1024 * 1024)).toFixed(0)}MB
            </div>
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleInputChange}
        disabled={disabled}
        style={{ display: 'none' }}
      />
    </div>
  );
}
