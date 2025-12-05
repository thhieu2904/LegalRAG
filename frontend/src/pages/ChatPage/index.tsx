/**
 * Chat Page
 */

import { useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useUIStore } from '@/stores/uiStore';
import { useTTS } from '@/hooks/useTTS';
import { ChatHistory, ChatInput } from '@/components/chat';
import type { FilterOptions } from '@/types/common.types';
import styles from './ChatPage.module.css';

export default function ChatPage() {
  const { messages, loading, sendMessage, selectDocument } = useChatStore();
  const { addToast } = useUIStore();
  const { speak } = useTTS();

  // Auto-speak new AI messages when TTS is enabled
  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;

    // Only auto-speak AI messages that are direct answers (not clarifications)
    if (
      lastMessage.role === 'assistant' &&
      !lastMessage.needs_clarification &&
      lastMessage.content
    ) {
      // Check if TTS is enabled
      const stored = localStorage.getItem('voiceSettings');
      let isTTSEnabled = false;
      let autoSpeak = true;

      if (stored) {
        try {
          const settings = JSON.parse(stored);
          isTTSEnabled = settings.ttsEnabled || false;
          // You can add a setting for auto-speak later
          autoSpeak = true;
        } catch (error) {
          console.error('Failed to parse voice settings:', error);
        }
      }

      if (isTTSEnabled && autoSpeak) {
        // Delay slightly to ensure content is rendered
        const timer = setTimeout(() => {
          if (lastMessage) {
            speak(lastMessage.content, `message-${lastMessage.id}`);
          }
        }, 300);

        return () => clearTimeout(timer);
      }
    }
  }, [messages, speak]);

  const handleSendMessage = async (message: string, filters: FilterOptions) => {
    try {
      await sendMessage(message, filters);
    } catch (error) {
      addToast({
        type: 'error',
        message: error instanceof Error ? error.message : 'Đã xảy ra lỗi khi gửi tin nhắn',
      });
    }
  };

  const handleSelectDocument = async (
    originalQuestion: string,
    documentId: string,
    documentTitle: string
  ) => {
    try {
      await selectDocument(originalQuestion, documentId, documentTitle);
    } catch (error) {
      addToast({
        type: 'error',
        message: error instanceof Error ? error.message : 'Đã xảy ra lỗi khi xử lý yêu cầu',
      });
    }
  };

  return (
    <div className={styles.chatPage}>
      {/* Messages History */}
      <ChatHistory messages={messages} loading={loading} onSelectDocument={handleSelectDocument} />

      {/* Input Area */}
      <ChatInput onSend={handleSendMessage} disabled={loading} />
    </div>
  );
}
