/**
 * CreateCollectionModal Component
 * Modal form for creating new collection with auto-slug generation
 */

import { useState, useEffect, type ChangeEvent, type FormEvent } from 'react';
import { X, AlertCircle, Loader2 } from 'lucide-react';
import { useAdminStore } from '@/stores/adminStore';
import { IconPicker } from '@/components/admin/IconPicker';
import { ColorPicker } from '@/components/admin/ColorPicker';
import { slugify, isValidSlug } from '@/utils/helpers/slugify';
import type {
  CreateCollectionModalProps,
  CreateCollectionFormData,
  FormErrors,
} from './CreateCollectionModal.types';
import styles from './CreateCollectionModal.module.css';

const INITIAL_FORM_DATA: CreateCollectionFormData = {
  display_name: '',
  name: '',
  description: '',
  icon: 'FolderOpen',
  color: '#3b82f6',
};

export const CreateCollectionModal = ({
  isOpen,
  onClose,
  onSuccess,
}: CreateCollectionModalProps) => {
  const { collections, addCollection } = useAdminStore();
  const [formData, setFormData] = useState<CreateCollectionFormData>(INITIAL_FORM_DATA);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSlugManuallyEdited, setIsSlugManuallyEdited] = useState(false);

  // Reset form when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setFormData(INITIAL_FORM_DATA);
      setErrors({});
      setIsSubmitting(false);
      setIsSlugManuallyEdited(false);
    }
  }, [isOpen]);

  // Auto-generate slug from display_name
  const handleDisplayNameChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData((prev) => ({
      ...prev,
      display_name: value,
      // Only auto-gen if user hasn't manually edited slug
      name: isSlugManuallyEdited ? prev.name : slugify(value),
    }));

    // Clear display_name error
    if (errors.display_name) {
      setErrors((prev) => ({ ...prev, display_name: undefined }));
    }
  };

  const handleSlugChange = (e: ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData((prev) => ({ ...prev, name: value }));
    setIsSlugManuallyEdited(true);

    // Clear slug error
    if (errors.name) {
      setErrors((prev) => ({ ...prev, name: undefined }));
    }
  };

  const handleDescriptionChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setFormData((prev) => ({ ...prev, description: e.target.value }));
  };

  const handleIconSelect = (icon: string) => {
    setFormData((prev) => ({ ...prev, icon }));
  };

  const handleColorSelect = (color: string) => {
    setFormData((prev) => ({ ...prev, color }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Display name required
    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Tên bộ sưu tập là bắt buộc';
    }

    // Slug required
    if (!formData.name.trim()) {
      newErrors.name = 'Slug là bắt buộc';
    } else if (!isValidSlug(formData.name)) {
      newErrors.name = 'Slug chỉ được chứa chữ thường, số và dấu gạch ngang';
    } else {
      // Check unique slug
      const isDuplicate = collections.some(
        (col: { name: string }) => col.name.toLowerCase() === formData.name.toLowerCase()
      );
      if (isDuplicate) {
        newErrors.name = 'Slug đã tồn tại. Vui lòng chọn slug khác';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle submit
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);

    try {
      await addCollection({
        name: formData.name,
        display_name: formData.display_name,
        description: formData.description || undefined,
        icon: formData.icon,
        color: formData.color,
      });

      // Success
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to create collection:', error);
      setErrors({
        display_name: 'Tạo bộ sưu tập thất bại. Vui lòng thử lại.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Close on backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
    }
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) return null;

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.modal}>
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>Tạo bộ sưu tập mới</h2>
          <button
            type="button"
            onClick={onClose}
            className={styles.closeButton}
            disabled={isSubmitting}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Display Name */}
          <div className={styles.formGroup}>
            <label htmlFor="display_name" className={styles.label}>
              Tên bộ sưu tập <span className={styles.required}>*</span>
            </label>
            <input
              id="display_name"
              type="text"
              value={formData.display_name}
              onChange={handleDisplayNameChange}
              placeholder="Ví dụ: Bộ luật Dân sự"
              className={`${styles.input} ${errors.display_name ? styles.inputError : ''}`}
              disabled={isSubmitting}
            />
            {errors.display_name && (
              <div className={styles.errorMessage}>
                <AlertCircle size={14} />
                <span>{errors.display_name}</span>
              </div>
            )}
          </div>

          {/* Slug */}
          <div className={styles.formGroup}>
            <label htmlFor="name" className={styles.label}>
              Slug (URL) <span className={styles.required}>*</span>
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={handleSlugChange}
              placeholder="bo-luat-dan-su"
              className={`${styles.input} ${errors.name ? styles.inputError : ''}`}
              disabled={isSubmitting}
            />
            <p className={styles.helperText}>
              {isSlugManuallyEdited
                ? 'Bạn đã chỉnh sửa slug thủ công'
                : 'Slug sẽ tự động tạo từ tên bộ sưu tập'}
            </p>
            {errors.name && (
              <div className={styles.errorMessage}>
                <AlertCircle size={14} />
                <span>{errors.name}</span>
              </div>
            )}
          </div>

          {/* Description */}
          <div className={styles.formGroup}>
            <label htmlFor="description" className={styles.label}>
              Mô tả
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={handleDescriptionChange}
              placeholder="Mô tả ngắn về bộ sưu tập này..."
              rows={3}
              className={styles.textarea}
              disabled={isSubmitting}
            />
          </div>

          {/* Icon Picker */}
          <div className={styles.formGroup}>
            <label className={styles.label}>Icon</label>
            <IconPicker selectedIcon={formData.icon} onSelectIcon={handleIconSelect} />
          </div>

          {/* Color Picker */}
          <div className={styles.formGroup}>
            <label className={styles.label}>Màu sắc</label>
            <ColorPicker
              selectedColor={formData.color}
              selectedIcon={formData.icon}
              onSelectColor={handleColorSelect}
            />
          </div>

          {/* Actions */}
          <div className={styles.actions}>
            <button
              type="button"
              onClick={onClose}
              className={styles.cancelButton}
              disabled={isSubmitting}
            >
              Hủy
            </button>
            <button type="submit" className={styles.submitButton} disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 size={18} className={styles.spinner} />
                  Đang tạo...
                </>
              ) : (
                'Tạo bộ sưu tập'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
