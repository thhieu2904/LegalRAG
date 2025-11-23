/**
 * ChatInput Component Types
 */

import type { FilterOptions } from '@/types/common.types';

export interface ChatInputProps {
  onSend: (message: string, filters: FilterOptions) => Promise<void>;
  disabled?: boolean;
}
