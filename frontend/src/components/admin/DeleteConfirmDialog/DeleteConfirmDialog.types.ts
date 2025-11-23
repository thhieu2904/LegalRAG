/**
 * DeleteConfirmDialog Types
 */

import type { Collection } from '@/types/admin.types';

export interface DeleteConfirmDialogProps {
  isOpen: boolean;
  collection: Collection | null;
  onClose: () => void;
  onConfirm: (collectionId: string) => Promise<void>;
}
