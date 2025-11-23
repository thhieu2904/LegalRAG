/**
 * SourceList Component Types
 */

import type { Source } from '@/types/common.types';

export interface SourceListProps {
  sources: Source[];
  query?: string; // User query for keyword highlighting
}
