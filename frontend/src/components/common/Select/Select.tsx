/**
 * Select Component
 */

import React, { useId } from 'react';
import styles from './Select.module.css';
import { cn } from '@/utils';
import type { SelectProps } from './Select.types';

export const Select = <T extends string | number = string>({
  options,
  value,
  defaultValue,
  placeholder = 'Chọn...',
  disabled = false,
  required = false,
  error,
  label,
  size = 'md',
  fullWidth = false,
  className,
  onChange,
  ariaLabel,
}: SelectProps<T>) => {
  const id = useId();
  const hasError = Boolean(error);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (onChange) {
      const selectedValue = e.target.value as T;
      onChange(selectedValue);
    }
  };

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
          styles.selectWrapper,
          styles[size],
          hasError && styles.error,
          disabled && styles.disabled
        )}
      >
        <select
          id={id}
          className={styles.select}
          value={value}
          defaultValue={defaultValue}
          disabled={disabled}
          required={required}
          onChange={handleChange}
          aria-label={ariaLabel || label}
          aria-invalid={hasError}
          aria-describedby={hasError ? `${id}-error` : undefined}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={String(option.value)} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>

        <span className={styles.arrow} aria-hidden="true">
          ▼
        </span>
      </div>

      {error && (
        <span id={`${id}-error`} className={styles.errorMessage} role="alert">
          {error}
        </span>
      )}
    </div>
  );
};
