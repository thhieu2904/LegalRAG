/**
 * ChatHistory Component Types
 */

import type { ChatMessage } from '@/types/chat.types';

export interface ChatHistoryProps {
  messages: ChatMessage[];
  loading: boolean;
}
