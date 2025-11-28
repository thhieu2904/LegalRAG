/**
 * ChatInput Component
 * Simple text input for legal Q&A
 */

import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import type { FilterOptions } from '@/types/common.types';
import styles from './ChatInput.module.css';
import type { ChatInputProps } from './ChatInput.types';

export const ChatInput = ({ onSend, disabled = false }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [filters] = useState<FilterOptions>({});
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;

    await onSend(input.trim(), filters);
    setInput('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const maxLength = 1000;
  const charCount = input.length;
  const isNearLimit = charCount > maxLength * 0.8;

  return (
    <div className={styles.chatInput}>
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* Input form */}
        <div className={styles.inputArea}>
          <div className={styles.editorRow}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi về pháp luật..."
              className={styles.textarea}
              rows={1}
              maxLength={maxLength}
              disabled={disabled}
            />

            <div className={styles.buttonGroup}>
              <button
                type="submit"
                disabled={!input.trim() || disabled}
                className={styles.sendButton}
                title="Gửi tin nhắn (Enter)"
              >
                {disabled ? <Loader2 size={20} className={styles.spinner} /> : <Send size={20} />}
              </button>
            </div>
          </div>
          <div className={styles.footer}>
            <span className={styles.hint}>Enter để gửi • Shift+Enter để xuống dòng</span>
            <span className={`${styles.counter} ${isNearLimit ? styles.counterWarning : ''}`}>
              {charCount}/{maxLength}
            </span>
          </div>
        </div>
      </form>
    </div>
  );
};
