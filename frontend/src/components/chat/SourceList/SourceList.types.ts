/**
 * SourceList Component Types
 */

import type { Source, FormInfo } from '@/types/common.types';

export interface SourceListProps {
  sources: Source[];
  forms?: FormInfo[]; // Forms attached to source documents
  query?: string; // User query for keyword highlighting
}
