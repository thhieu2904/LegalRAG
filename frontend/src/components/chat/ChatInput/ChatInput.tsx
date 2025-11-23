/**
 * ChatInput Component
 */

import { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { VoiceInput } from '../VoiceInput';
// import { Filter } from 'lucide-react'; // TODO: Re-enable when filters fixed
// import { Select } from '@/components/common'; // TODO: Re-enable when filters fixed
// import { MA_KHOA_OPTIONS, MON_HOC_OPTIONS, HOC_KY_OPTIONS } from '@/constants/app.constants'; // TODO: Replace with new schema
import type { FilterOptions } from '@/types/common.types';
import styles from './ChatInput.module.css';
import type { ChatInputProps } from './ChatInput.types';

export const ChatInput = ({ onSend, disabled = false }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [filters] = useState<FilterOptions>({}); // TODO: Re-enable setFilters when filters fixed
  // const [showFilters, setShowFilters] = useState(false); // TODO: Re-enable when filters fixed
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

  // Voice input handlers
  const handleTranscriptChange = (transcript: string) => {
    // Show interim transcript (optional - can be used for live preview)
    console.log('Interim:', transcript);
  };

  const handleFinalTranscript = (transcript: string) => {
    // Append final transcript to input
    setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
  };

  const handleAutoSend = async (transcript: string) => {
    // Auto-send when recording stops (if enabled in settings)
    if (!disabled) {
      await onSend(transcript.trim(), filters);
      setInput('');
    }
  };

  return (
    <div className={styles.chatInput}>
      <form onSubmit={handleSubmit} className={styles.form}>
        {/* TODO: Filters - Disabled temporarily due to schema mismatch
          Current FilterOptions uses old schema (ma_khoa, ma_mon_hoc, loai_noi_dung)
          Backend expects new schema (ma_chuyen_nganh, ma_mon, upload_type)
          Need to:
          1. Update FilterOptions type to match new schema
          2. Update constants (MA_KHOA_OPTIONS -> CHUYEN_NGANH_OPTIONS)
          3. Fetch dropdown data from backend (/admin/chuyen-nganh, /admin/mon-hoc)
          4. Update filter UI accordingly
      */}
        {/* <div className={styles.filtersSection}>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={styles.filterToggle}
          type="button"
        >
          <Filter size={16} />
          <span>Bộ lọc</span>
          {Object.keys(filters).length > 0 && (
            <span className={styles.filterBadge}>{Object.keys(filters).length}</span>
          )}
        </button>

        {showFilters && (
          <div className={styles.filters}>
            <Select
              options={MA_KHOA_OPTIONS}
              value={filters.ma_khoa}
              onChange={(value) => setFilters({ ...filters, ma_khoa: value || undefined })}
              placeholder="Chọn khoa"
              size="sm"
            />
            <Select
              options={MON_HOC_OPTIONS}
              value={filters.ma_mon_hoc}
              onChange={(value) => setFilters({ ...filters, ma_mon_hoc: value || undefined })}
              placeholder="Chọn môn học"
              size="sm"
            />
            <Select
              options={HOC_KY_OPTIONS}
              value={filters.hoc_ky}
              onChange={(value) =>
                setFilters({
                  ...filters,
                  hoc_ky: value as number | undefined,
                })
              }
              placeholder="Chọn học kỳ"
              size="sm"
            />
          </div>
        )}
      </div> */}

        {/* Input form */}
        <div className={styles.inputArea}>
          <div className={styles.editorRow}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Nhập câu hỏi của bạn..."
              className={styles.textarea}
              rows={1}
              maxLength={maxLength}
              disabled={disabled}
            />

            <div className={styles.buttonGroup}>
              <VoiceInput
                onTranscriptChange={handleTranscriptChange}
                onFinalTranscript={handleFinalTranscript}
                onAutoSend={handleAutoSend}
                disabled={disabled}
              />

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
