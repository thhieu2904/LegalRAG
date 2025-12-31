/**
 * EditCollectionModal Component
 * Modal form for editing existing collection (slug is readonly)
 */

import { useState, useEffect, type ChangeEvent, type FormEvent } from 'react';
import { X, AlertCircle, Loader2 } from 'lucide-react';
import { useAdminStore } from '@/stores/adminStore';
import { IconPicker } from '@/components/admin/IconPicker';
import { ColorPicker } from '@/components/admin/ColorPicker';
import type {
  EditCollectionModalProps,
  EditCollectionFormData,
  FormErrors,
} from './EditCollectionModal.types';
import styles from './EditCollectionModal.module.css';

export const EditCollectionModal = ({
  isOpen,
  collection,
  onClose,
  onSuccess,
}: EditCollectionModalProps) => {
  const { editCollection } = useAdminStore();
  const [formData, setFormData] = useState<EditCollectionFormData>({
    display_name: '',
    description: '',
    icon: 'FolderOpen',
    color: '#3b82f6',
    is_active: true,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Populate form when collection changes
  useEffect(() => {
    if (isOpen && collection) {
      setFormData({
        display_name: collection.display_name,
        description: collection.description || '',
        icon: collection.icon,
        color: collection.color,
        is_active: collection.is_active,
      });
      setErrors({});
      setIsSubmitting(false);
    }
  }, [isOpen, collection]);

  const handleDisplayNameChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, display_name: e.target.value }));
    if (errors.display_name) {
      setErrors((prev) => ({ ...prev, display_name: undefined }));
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

  const handleActiveToggle = (e: ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, is_active: e.target.checked }));
  };

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.display_name.trim()) {
      newErrors.display_name = 'Tên bộ sưu tập là bắt buộc';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle submit
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!collection || !validateForm()) return;

    setIsSubmitting(true);

    try {
      await editCollection(collection.id, {
        display_name: formData.display_name,
        description: formData.description || undefined,
        icon: formData.icon,
        color: formData.color,
        is_active: formData.is_active,
      });

      // Success
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to update collection:', error);
      setErrors({
        display_name: 'Cập nhật bộ sưu tập thất bại. Vui lòng thử lại.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Close handlers
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

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

  if (!isOpen || !collection) return null;

  return (
    <div className={styles.backdrop} onClick={handleBackdropClick}>
      <div className={styles.modal}>
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>Chỉnh sửa bộ sưu tập</h2>
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

          {/* Slug (Readonly) */}
          <div className={styles.formGroup}>
            <label htmlFor="name" className={styles.label}>
              Slug (URL) <span className={styles.readonlyBadge}>Không thể chỉnh sửa</span>
            </label>
            <input
              id="name"
              type="text"
              value={collection.name}
              className={`${styles.input} ${styles.inputReadonly}`}
              disabled
              readOnly
            />
            <p className={styles.helperText}>Slug không thể thay đổi sau khi tạo</p>
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

          {/* Active Toggle */}
          <div className={styles.formGroup}>
            <label className={styles.checkboxLabel}>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={handleActiveToggle}
                className={styles.checkbox}
                disabled={isSubmitting}
              />
              <span>Kích hoạt bộ sưu tập</span>
            </label>
            <p className={styles.helperText}>
              Bộ sưu tập bị vô hiệu hóa sẽ không hiển thị trong tìm kiếm
            </p>
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
                  Đang lưu...
                </>
              ) : (
                'Lưu thay đổi'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
