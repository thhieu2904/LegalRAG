/**
 * CollectionCard Component Types
 */

export interface CollectionCardProps {
  id: string;
  name: string;
  slug: string;
  description?: string;
  icon: string;
  color: string;
  document_count: number;
  total_chunks: number;
  is_active: boolean;
  created_at: string;
  onClick?: (id: string) => void;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}
