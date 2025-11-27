/**
 * ChatMessage Component
 */

import { useState } from 'react';
import { User, FileText } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatTimeAgo } from '@/utils/formatters/date';
import { cn } from '@/utils/helpers/className';
import { SourceViewer } from '../SourceViewer';
import styles from './ChatMessage.module.css';
import type { ChatMessageProps } from './ChatMessage.types';

export const ChatMessage = ({ message, onSelectDocument }: ChatMessageProps) => {
  const [showSourceViewer, setShowSourceViewer] = useState(false);
  const isUser = message.role === 'user';
  const isAI = message.role === 'assistant';

  if (showSourceViewer && message.sources) {
    return (
      <SourceViewer
        sources={message.sources}
        query={message.query}
        onClose={() => setShowSourceViewer(false)}
      />
    );
  }

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

        {/* Timestamp */}
        <time className={styles.timestamp}>{formatTimeAgo(message.timestamp)}</time>

        {/* Sources Button (AI only) - Compact version */}
        {isAI && message.sources && message.sources.length > 0 && (
          <button
            onClick={() => setShowSourceViewer(true)}
            className={styles.sourcesButton}
            aria-label={`Xem ${message.sources.length} nguồn tham khảo`}
          >
            📄 {message.sources.length} nguồn tham khảo
          </button>
        )}

        {/* Metadata - Hidden for end users (uncomment for debugging) */}
        {isAI && (message.tokens || message.took_ms) && (
          <div className={styles.metadata}>
            {message.took_ms && <span>⏱️ {message.took_ms}ms</span>}
            {message.tokens && <span>🎯 {message.tokens} tokens</span>}
          </div>
        )}
      </div>
    </div>
  );
};
