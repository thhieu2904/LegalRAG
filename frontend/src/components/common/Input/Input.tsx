/**
 * Input Component
 */

import React, { useId } from 'react';
import styles from './Input.module.css';
import { cn } from '@/utils';
import type { InputProps } from './Input.types';

export const Input: React.FC<InputProps> = ({
  type = 'text',
  size = 'md',
  value,
  defaultValue,
  placeholder,
  disabled = false,
  readOnly = false,
  required = false,
  error,
  label,
  leftIcon,
  rightIcon,
  fullWidth = false,
  maxLength,
  autoFocus = false,
  className,
  onChange,
  onFocus,
  onBlur,
  onKeyDown,
  ariaLabel,
}) => {
  const id = useId();
  const hasError = Boolean(error);

  return (
    <div className={cn(styles.wrapper, fullWidth && styles.fullWidth, className)}>
      {label && (
        <label htmlFor={id} className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}

      <div
        className={cn(
          styles.inputWrapper,
          styles[size],
          hasError && styles.error,
          disabled && styles.disabled
        )}
      >
        {leftIcon && <span className={styles.leftIcon}>{leftIcon}</span>}

        <input
          id={id}
          type={type}
          className={styles.input}
          value={value}
          defaultValue={defaultValue}
          placeholder={placeholder}
          disabled={disabled}
          readOnly={readOnly}
          required={required}
          maxLength={maxLength}
          autoFocus={autoFocus}
          onChange={onChange}
          onFocus={onFocus}
          onBlur={onBlur}
          onKeyDown={onKeyDown}
          aria-label={ariaLabel || label}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${id}-error` : undefined}
        />

        {rightIcon && <span className={styles.rightIcon}>{rightIcon}</span>}
      </div>

      {error && (
        <span id={`${id}-error`} className={styles.errorMessage} role="alert">
          {error}
        </span>
      )}
    </div>
  );
};
