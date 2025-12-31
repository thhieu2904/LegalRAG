/**
 * ConfirmModal Component
 *
 * A reusable confirmation modal with icon, title, message, and action buttons
 */

import type { ReactNode } from 'react';
import { X, AlertTriangle, CheckCircle, Info, AlertCircle } from 'lucide-react';
import styles from './ConfirmModal.module.css';

export type ModalVariant = 'warning' | 'success' | 'info' | 'error';

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string | ReactNode;
  confirmText?: string;
  cancelText?: string;
  variant?: ModalVariant;
  confirmDanger?: boolean;
}

const iconMap = {
  warning: AlertTriangle,
  success: CheckCircle,
  info: Info,
  error: AlertCircle,
};

export const ConfirmModal = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Xác nhận',
  cancelText = 'Hủy',
  variant = 'warning',
  confirmDanger = false,
}: ConfirmModalProps) => {
  if (!isOpen) return null;

  const Icon = iconMap[variant];

  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={handleBackdropClick}>
      <div className={styles.modal}>
        {/* Header */}
        <div className={styles.header}>
          <div className={`${styles.iconWrapper} ${styles[variant]}`}>
            <Icon className={styles.icon} size={24} />
          </div>
          <button className={styles.closeButton} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          <h2 className={styles.title}>{title}</h2>
          <div className={styles.message}>{message}</div>
        </div>

        {/* Actions */}
        <div className={styles.actions}>
          <button className={styles.cancelButton} onClick={onClose}>
            {cancelText}
          </button>
          <button
            className={confirmDanger ? styles.dangerButton : styles.confirmButton}
            onClick={handleConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};
