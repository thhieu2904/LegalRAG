/**
 * Number Formatting Utilities
 */

/**
 * Format number with thousand separators
 * @param num - Number to format
 */
export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('vi-VN').format(num);
};

/**
 * Format bytes to human-readable size
 * @param bytes - Size in bytes
 * @param decimals - Number of decimal places (default: 2)
 */
export const formatFileSize = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

/**
 * Format percentage
 * @param value - Value between 0 and 1
 * @param decimals - Number of decimal places (default: 0)
 */
export const formatPercentage = (value: number, decimals = 0): string => {
  return (value * 100).toFixed(decimals) + '%';
};

/**
 * Format milliseconds to seconds
 * @param ms - Milliseconds
 * @param decimals - Number of decimal places (default: 1)
 */
export const formatMs = (ms: number, decimals = 1): string => {
  return (ms / 1000).toFixed(decimals) + 's';
};

/**
 * Format similarity score to percentage
 */
export const formatSimilarity = (score: number): string => {
  return Math.round(score * 100) + '%';
};
