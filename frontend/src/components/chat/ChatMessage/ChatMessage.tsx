/**
 * ChatMessage Component
 * Displays chat messages with legal document sources
 */

import { useState, useEffect } from 'react';
import { User, FileText, Clock, Zap, Play, Pause, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useTTS } from '@/hooks/useTTS';
import { formatTimeAgo } from '@/utils/formatters/date';
import { cn } from '@/utils/helpers/className';
import { SourceList } from '../SourceList';
import styles from './ChatMessage.module.css';
import type { ChatMessageProps } from './ChatMessage.types';

/**
 * Format processing time for display
 */
const formatProcessingTime = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  return `${(ms / 1000).toFixed(1)}s`;
};

export const ChatMessage = ({ message, onSelectDocument }: ChatMessageProps) => {
  const isUser = message.role === 'user';
  const isAI = message.role === 'assistant';
  const { speak, pause, resume, stop, state: ttsState } = useTTS();
  const [isThisMessagePlaying, setIsThisMessagePlaying] = useState(false);

  // Check if TTS is enabled
  const isTTSEnabled = (() => {
    const stored = localStorage.getItem('voiceSettings');
    if (stored) {
      try {
        return JSON.parse(stored).ttsEnabled || false;
      } catch {
        return false;
      }
    }
    return false;
  })();

  // Update state based on TTS state
  useEffect(() => {
    if (ttsState.utteranceId === `message-${message.id}`) {
      setIsThisMessagePlaying(ttsState.isPlaying);
    } else if (isThisMessagePlaying && !ttsState.isPlaying) {
      setIsThisMessagePlaying(false);
    }
  }, [ttsState.isPlaying, ttsState.utteranceId, message.id, isThisMessagePlaying]);

  const handlePlayTTS = () => {
    if (isThisMessagePlaying) {
      if (ttsState.isPaused) {
        resume();
      } else {
        pause();
      }
    } else {
      // Stop any other message that's playing and play this one
      stop();
      speak(message.content, `message-${message.id}`);
      setIsThisMessagePlaying(true);
    }
  };

  const handleStopTTS = () => {
    stop();
    setIsThisMessagePlaying(false);
  };

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

        {/* TTS Controls for AI Messages */}
        {isAI && isTTSEnabled && !message.needs_clarification && (
          <div
            style={{
              display: 'flex',
              gap: '8px',
              marginTop: '8px',
              alignItems: 'center',
            }}
          >
            <button
              onClick={handlePlayTTS}
              title={
                isThisMessagePlaying
                  ? ttsState.isPaused
                    ? 'Tiếp tục'
                    : 'Tạm dừng'
                  : 'Đọc thành tiếng'
              }
              style={{
                padding: '6px 10px',
                backgroundColor: isThisMessagePlaying ? '#ff9800' : '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px',
                fontWeight: '500',
              }}
            >
              {isThisMessagePlaying && ttsState.isPaused ? (
                <>
                  <Play size={14} />
                  Tiếp tục
                </>
              ) : isThisMessagePlaying ? (
                <>
                  <Pause size={14} />
                  Tạm dừng
                </>
              ) : (
                <>
                  <Play size={14} />
                  Đọc
                </>
              )}
            </button>
            {isThisMessagePlaying && (
              <button
                onClick={handleStopTTS}
                title="Dừng đọc"
                style={{
                  padding: '6px 10px',
                  backgroundColor: '#f44336',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  fontSize: '12px',
                  fontWeight: '500',
                }}
              >
                <X size={14} />
                Dừng
              </button>
            )}
          </div>
        )}

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

        {/* Metadata: Timestamp and Processing Time */}
        <div className={styles.messageFooter}>
          <time className={styles.timestamp}>{formatTimeAgo(message.timestamp)}</time>

          {/* Processing time for AI messages */}
          {isAI && message.took_ms && (
            <span className={styles.processingTime} title="Thời gian xử lý">
              <Zap size={12} />
              {formatProcessingTime(message.took_ms)}
            </span>
          )}

          {/* Token count for AI messages */}
          {isAI && message.tokens && message.tokens > 0 && (
            <span className={styles.tokenCount} title="Số token sử dụng">
              <Clock size={12} />
              {message.tokens} tokens
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
