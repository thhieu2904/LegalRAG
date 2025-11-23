/**
 * Toast Component Types
 */

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastItemProps {
  id: string;
  type: ToastType;
  message: string;
  onClose: (id: string) => void;
}

export interface ToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center';
}
