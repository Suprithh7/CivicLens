/**
 * File utility functions
 * Helpers for file validation, formatting, and manipulation
 */

import { MAX_FILE_SIZE_BYTES, ALLOWED_FILE_TYPES, ERROR_FILE_TOO_LARGE, ERROR_INVALID_FILE_TYPE } from '../constants';

/**
 * Format file size in bytes to human-readable string
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted string (e.g., "1.5 MB")
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * Validate file type
 * @param {File} file - File to validate
 * @returns {{valid: boolean, error: string|null}}
 */
export function validateFileType(file) {
  if (!ALLOWED_FILE_TYPES.includes(file.type)) {
    return { valid: false, error: ERROR_INVALID_FILE_TYPE };
  }
  return { valid: true, error: null };
}

/**
 * Validate file size
 * @param {File} file - File to validate
 * @returns {{valid: boolean, error: string|null}}
 */
export function validateFileSize(file) {
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { valid: false, error: ERROR_FILE_TOO_LARGE };
  }
  return { valid: true, error: null };
}

/**
 * Validate file (type and size)
 * @param {File} file - File to validate
 * @returns {{valid: boolean, error: string|null}}
 */
export function validateFile(file) {
  const typeValidation = validateFileType(file);
  if (!typeValidation.valid) return typeValidation;

  const sizeValidation = validateFileSize(file);
  if (!sizeValidation.valid) return sizeValidation;

  return { valid: true, error: null };
}

/**
 * Get file extension from filename
 * @param {string} filename - Name of the file
 * @returns {string} File extension including the dot (e.g., ".pdf")
 */
export function getFileExtension(filename) {
  const lastDot = filename.lastIndexOf('.');
  return lastDot === -1 ? '' : filename.substring(lastDot).toLowerCase();
}
