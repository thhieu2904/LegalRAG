/**
 * Date Formatting Utilities
 */

import { format, formatDistanceToNow } from 'date-fns';
import { vi } from 'date-fns/locale';

/**
 * Format date to readable string
 * @param date - Date object or timestamp
 * @param pattern - Format pattern (default: 'dd/MM/yyyy HH:mm')
 */
export const formatDate = (date: Date | number, pattern = 'dd/MM/yyyy HH:mm'): string => {
  return format(date, pattern, { locale: vi });
};

/**
 * Format date to time ago (e.g., "2 phút trước")
 * @param date - Date object or timestamp
 */
export const formatTimeAgo = (date: Date | number): string => {
  return formatDistanceToNow(date, { addSuffix: true, locale: vi });
};

/**
 * Format date to short format (dd/MM/yyyy)
 */
export const formatShortDate = (date: Date | number): string => {
  return format(date, 'dd/MM/yyyy', { locale: vi });
};

/**
 * Format time only (HH:mm:ss)
 */
export const formatTime = (date: Date | number): string => {
  return format(date, 'HH:mm:ss', { locale: vi });
};
