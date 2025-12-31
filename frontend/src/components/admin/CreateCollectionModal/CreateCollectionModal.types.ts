/**
 * CreateCollectionModal Types
 */

export interface CreateCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export interface CreateCollectionFormData {
  display_name: string;
  name: string; // slug
  description: string;
  icon: string;
  color: string;
}

export interface FormErrors {
  display_name?: string;
  name?: string;
  description?: string;
}
