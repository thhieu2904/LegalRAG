/**
 * File Validation Utilities
 */

import { ALLOWED_FILE_TYPES, ALLOWED_FILE_EXTENSIONS, MAX_FILE_SIZE } from '@/constants';

/**
 * Validate file type
 * @param file - File to validate
 */
export const validateFileType = (file: File): boolean => {
  return ALLOWED_FILE_TYPES.includes(file.type);
};

/**
 * Validate file extension
 * @param filename - Filename to validate
 */
export const validateFileExtension = (filename: string): boolean => {
  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  return ALLOWED_FILE_EXTENSIONS.includes(extension);
};

/**
 * Validate file size
 * @param file - File to validate
 */
export const validateFileSize = (file: File): boolean => {
  return file.size <= MAX_FILE_SIZE;
};

/**
 * Validate file completely
 * @param file - File to validate
 * @returns { valid: boolean, error?: string }
 */
export const validateFile = (file: File): { valid: boolean; error?: string } => {
  if (!validateFileType(file)) {
    return {
      valid: false,
      error: `File type không được hỗ trợ. Chỉ chấp nhận: ${ALLOWED_FILE_EXTENSIONS.join(', ')}`,
    };
  }

  if (!validateFileExtension(file.name)) {
    return {
      valid: false,
      error: `File extension không hợp lệ. Chỉ chấp nhận: ${ALLOWED_FILE_EXTENSIONS.join(', ')}`,
    };
  }

  if (!validateFileSize(file)) {
    return {
      valid: false,
      error: `File quá lớn. Kích thước tối đa: ${MAX_FILE_SIZE / 1024 / 1024}MB`,
    };
  }

  return { valid: true };
};
