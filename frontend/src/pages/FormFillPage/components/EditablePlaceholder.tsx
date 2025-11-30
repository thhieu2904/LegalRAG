/**
 * EditablePlaceholder Component
 * Inline edit via popover - avoid focus issues completely
 * Follows frontend_old pattern for stability
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Edit3, Save, X } from 'lucide-react';
import styles from './EditablePlaceholder.module.css';

export interface EditablePlaceholderProps {
  fieldName: string;
  value?: string;
  placeholder?: string;
  onSave: (fieldName: string, value: string) => void;
  cccdValue?: string;
}

export const EditablePlaceholder: React.FC<EditablePlaceholderProps> = ({
  fieldName,
  value = '',
  placeholder = 'Nhập thông tin...',
  onSave,
  cccdValue,
}) => {
  const [inputValue, setInputValue] = useState(value);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync with external value changes
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // Auto focus input when popover opens
  useEffect(() => {
    if (isPopoverOpen && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isPopoverOpen]);

  const handleClick = () => {
    setIsPopoverOpen(true);
  };

  const handleSave = () => {
    onSave(fieldName, inputValue);
    setIsPopoverOpen(false);
  };

  const handleCancel = useCallback(() => {
    setInputValue(value);
    setIsPopoverOpen(false);
  }, [value]);

  // Close popover on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target as Node)) {
        handleCancel();
      }
    };

    if (isPopoverOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isPopoverOpen, handleCancel]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  // Display: Manual > CCCD > Placeholder
  const displayValue = value || cccdValue || '[Cần điền]';
  const hasValue = Boolean(value);
  const hasCCCDValue = Boolean(cccdValue);

  // Format field label
  const fieldLabel = fieldName
    .replace(/_/g, ' ')
    .replace(/^scan /, '')
    .replace(/^form /, '')
    .replace(/^./, (s) => s.toUpperCase());

  return (
    <span className={styles.container}>
      {/* Display element */}
      <span
        className={`${styles.display} ${hasValue ? styles.hasValue : styles.needsInput} ${hasCCCDValue ? styles.hasCCCD : ''}`}
        onClick={handleClick}
        title={`Click để chỉnh sửa • ${fieldLabel}`}
      >
        {displayValue}
        <Edit3 className={styles.editIcon} size={12} />
      </span>

      {/* Popover */}
      {isPopoverOpen && (
        <div className={styles.overlay}>
          <div ref={popoverRef} className={styles.popover}>
            <div className={styles.popoverHeader}>
              <h4>Chỉnh sửa</h4>
              <button className={styles.closeBtn} onClick={handleCancel} type="button">
                <X size={14} />
              </button>
            </div>

            <div className={styles.popoverBody}>
              <label className={styles.fieldLabel}>{fieldLabel}</label>

              {cccdValue && (
                <div className={styles.cccdRef}>
                  <span className={styles.cccdLabel}>📱 Từ CCCD:</span>
                  <span className={styles.cccdValue}>{cccdValue}</span>
                </div>
              )}

              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
                className={styles.input}
              />
            </div>

            <div className={styles.popoverFooter}>
              <button className={styles.cancelBtn} onClick={handleCancel} type="button">
                Hủy
              </button>
              <button className={styles.saveBtn} onClick={handleSave} type="button">
                <Save size={14} />
                Lưu
              </button>
            </div>
          </div>
        </div>
      )}
    </span>
  );
};
