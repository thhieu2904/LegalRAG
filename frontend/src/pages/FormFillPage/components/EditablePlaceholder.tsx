import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { Check, Edit3, X } from 'lucide-react';
import type { FormFieldConfig } from '../templates';
import { FieldDictation } from './FieldDictation';
import styles from './EditablePlaceholder.module.css';

export interface EditablePlaceholderProps {
  fieldName: string;
  value?: string;
  onSave: (fieldName: string, value: string) => void;
  config?: FormFieldConfig;
  cccdValue?: string;
  fromQr?: boolean;
}

function FieldEditor({ fieldName, value = '', onSave, config, cccdValue, onClose }: EditablePlaceholderProps & {
  onClose: () => void;
}) {
  const [inputValue, setInputValue] = useState(value);
  const [listening, setListening] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputId = useId();
  const label = config?.label ?? fieldName.replaceAll('_', ' ');
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    inputRef.current?.focus();
    return () => previous?.focus();
  }, []);
  const save = () => {
    if (listening) return;
    onSave(fieldName, inputValue);
    onClose();
  };
  return createPortal(
    <div className={styles.overlay} onMouseDown={(event) => {
      if (event.target === event.currentTarget) onClose();
    }}>
      <div ref={dialogRef} className={styles.popover} role="dialog" aria-modal="true" aria-label={label} onKeyDown={(event) => {
        if (event.key === 'Escape') { event.stopPropagation(); onClose(); }
        if (event.key === 'Tab') {
          const controls = dialogRef.current?.querySelectorAll<HTMLElement>('button:not(:disabled),textarea:not(:disabled),input:not(:disabled)');
          const first = controls?.[0];
          const last = controls?.[controls.length - 1];
          if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
          if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
        }
      }}>
        <div className={styles.popoverHeader}>
          <h4>{config?.group ?? 'Chỉnh sửa ô'}</h4>
          <button type="button" className={styles.closeBtn} aria-label="Đóng ô đang sửa" onClick={onClose}><X size={14} /></button>
        </div>
        <div className={styles.popoverBody}>
          <label htmlFor={inputId} className={styles.fieldLabel}>{label}</label>
          {config?.hint && <p className={styles.hint}>{config.hint}</p>}
          {cccdValue && <div className={styles.cccdRef}>
            <span>Gợi ý từ QR: {cccdValue}</span>
            <button type="button" className={styles.voiceButton} disabled={listening} onClick={() => setInputValue(cccdValue)}>Dùng gợi ý</button>
          </div>}
          <textarea
            id={inputId} ref={inputRef} value={inputValue} maxLength={2000} rows={3}
            readOnly={listening} aria-busy={listening}
            onChange={(event) => setInputValue(event.target.value)}
            placeholder={`Nhập ${label.toLowerCase()}`} className={styles.input}
          />
          <FieldDictation value={inputValue} onChange={setInputValue} onListeningChange={setListening} />
        </div>
        <div className={styles.popoverFooter}>
          <button type="button" className={styles.cancelBtn} onClick={onClose}>Hủy</button>
          <button type="button" className={styles.saveBtn} disabled={listening} onClick={save}><Check size={14} />Xong</button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

export const EditablePlaceholder = (props: EditablePlaceholderProps) => {
  const [open, setOpen] = useState(false);
  const label = props.config?.label ?? props.fieldName.replaceAll('_', ' ');
  return (
    <span className={styles.container}>
      <button
        type="button"
        className={`${styles.display} ${props.value ? styles.hasValue : styles.needsInput} ${props.fromQr ? styles.hasCCCD : ''}`}
        onClick={() => setOpen(true)} aria-label={`Điền ${label}`}
        title={`${label}${props.fromQr ? ' — lấy từ QR, cần kiểm tra' : ''}`}
      >
        {props.value || `[${label}]`}<Edit3 className={styles.editIcon} size={12} />
      </button>
      {open && <FieldEditor {...props} onClose={() => setOpen(false)} />}
    </span>
  );
};
