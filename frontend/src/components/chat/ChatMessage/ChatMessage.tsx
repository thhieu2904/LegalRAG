/**
 * ChatMessage Component
 * Displays chat messages with legal document sources
 */

import { User, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatTimeAgo } from '@/utils/formatters/date';
import { cn } from '@/utils/helpers/className';
import { SourceList } from '../SourceList';
import styles from './ChatMessage.module.css';
import type { ChatMessageProps } from './ChatMessage.types';

export const ChatMessage = ({ message, onSelectDocument }: ChatMessageProps) => {
  const isUser = message.role === 'user';
  const isAI = message.role === 'assistant';

  return (
    <div className={cn(styles.chatMessage, isUser && styles.userMessage, isAI && styles.aiMessage)}>
      {/* Avatar */}
      <div className={styles.avatar}>
        {isUser ? (
          <User size={20} />
        ) : (
          <img src="/LOGO_HCC.jpg" alt="AI Assistant" className={styles.botAvatar} />
        )}
      </div>

      {/* Content */}
      <div className={styles.content}>
        {/* Message text with markdown */}
        <div className={styles.text}>
          {isAI ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          ) : (
            <p>{message.content}</p>
          )}
        </div>

        {/* Document Options (Clarification) */}
        {isAI && message.needs_clarification && message.document_options && (
          <div className={styles.documentOptions}>
            {message.document_options.map((option) => (
              <button
                key={option.document_id}
                className={styles.documentButton}
                onClick={() =>
                  onSelectDocument?.(
                    message.originalQuestion || '',
                    option.document_id,
                    option.title
                  )
                }
              >
                <FileText size={16} className={styles.documentIcon} />
                <div className={styles.documentInfo}>
                  <span className={styles.documentTitle}>{option.title}</span>
                  <span className={styles.documentConfidence}>
                    Độ phù hợp: {Math.round(option.confidence * 100)}%
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Sources - Show inline for AI messages */}
        {isAI && message.sources && message.sources.length > 0 && !message.needs_clarification && (
          <SourceList sources={message.sources} forms={message.forms} />
        )}

        {/* Timestamp */}
        <time className={styles.timestamp}>{formatTimeAgo(message.timestamp)}</time>
      </div>
    </div>
  );
};
