/**
 * Toast Component
 */

import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';
import styles from './Toast.module.css';
import { cn } from '@/utils';
import type { ToastItemProps, ToastContainerProps } from './Toast.types';
import { useUIStore } from '@/stores';

// Toast Item Component
export const ToastItem: React.FC<ToastItemProps> = ({ id, type, message, onClose }) => {
  const icons = {
    success: <CheckCircle size={20} />,
    error: <XCircle size={20} />,
    warning: <AlertCircle size={20} />,
    info: <Info size={20} />,
  };

  return (
    <div className={cn(styles.toast, styles[type])} role="alert" aria-live="polite">
      <div className={styles.icon}>{icons[type]}</div>
      <p className={styles.message}>{message}</p>
      <button
        className={styles.closeButton}
        onClick={() => onClose(id)}
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </div>
  );
};

// Toast Container Component
export const ToastContainer: React.FC<ToastContainerProps> = ({ position = 'top-right' }) => {
  const { toasts, removeToast } = useUIStore();

  return (
    <div className={cn(styles.container, styles[position])}>
      {toasts.map((toast) => (
        <ToastItem key={toast.id} {...toast} onClose={removeToast} />
      ))}
    </div>
  );
};
