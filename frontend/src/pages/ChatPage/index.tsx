/**
 * Chat Page
 */

import { useChatStore } from '@/stores/chatStore';
import { useUIStore } from '@/stores/uiStore';
import { ChatHistory, ChatInput } from '@/components/chat';
import type { FilterOptions } from '@/types/common.types';
import styles from './ChatPage.module.css';

export default function ChatPage() {
  const { messages, loading, sendMessage } = useChatStore();
  const { addToast } = useUIStore();

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

  return (
    <div className={styles.chatPage}>
      {/* Messages History */}
      <ChatHistory messages={messages} loading={loading} />

      {/* Input Area */}
      <ChatInput onSend={handleSendMessage} disabled={loading} />
    </div>
  );
}
