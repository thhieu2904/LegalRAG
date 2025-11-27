/**
 * ChatMessage Component Types
 */

import type { ChatMessage as ChatMessageType } from '@/types/chat.types';

export interface ChatMessageProps {
  message: ChatMessageType;
  onSelectDocument?: (originalQuestion: string, documentId: string, documentTitle: string) => void;
}
