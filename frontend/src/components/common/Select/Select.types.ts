/**
 * Select Component Types
 */

export interface SelectOption<T = string | number> {
  value: T;
  label: string;
  disabled?: boolean;
}

export type SelectSize = 'sm' | 'md' | 'lg';

export interface SelectProps<T = string | number> {
  options: SelectOption<T>[];
  value?: T;
  defaultValue?: T;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  error?: string;
  label?: string;
  size?: SelectSize;
  fullWidth?: boolean;
  className?: string;
  onChange?: (value: T) => void;
  ariaLabel?: string;
}
