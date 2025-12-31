/**
 * EditCollectionModal Types
 */

import type { Collection } from '@/types/admin.types';

export interface EditCollectionModalProps {
  isOpen: boolean;
  collection: Collection | null;
  onClose: () => void;
  onSuccess?: () => void;
}

export interface EditCollectionFormData {
  display_name: string;
  description: string;
  icon: string;
  color: string;
  is_active: boolean;
}

export interface FormErrors {
  display_name?: string;
  description?: string;
}
