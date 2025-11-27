/**
 * ChatHistory Component
 */

import { useEffect, useRef } from 'react';
import { ChatMessage } from '../ChatMessage';
import { EmptyState } from '../EmptyState';
import { TypingIndicator } from '../TypingIndicator';
import styles from './ChatHistory.module.css';
import type { ChatHistoryProps } from './ChatHistory.types';

export const ChatHistory = ({ messages, loading, onSelectDocument }: ChatHistoryProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new message arrives or loading state changes
  useEffect(() => {
    // Use setTimeout to ensure DOM has updated before scrolling
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 0);
  }, [messages, loading]);

  return (
    <div className={styles.chatHistory} ref={scrollRef}>
      <div className={styles.messages}>
        {messages.length === 0 && !loading ? (
          <EmptyState />
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} onSelectDocument={onSelectDocument} />
            ))}
            {loading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};
