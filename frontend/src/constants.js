/**
 * Application-wide constants
 * Centralized location for all configuration values and magic numbers
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_VERSION = 'v1';

// File Upload Configuration
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB
export const MAX_FILE_SIZE_MB = 10;
export const ALLOWED_FILE_TYPES = ['application/pdf'];
export const ALLOWED_FILE_EXTENSIONS = ['.pdf'];

// Pagination
export const DEFAULT_PAGE_SIZE = 12;
export const ITEMS_PER_PAGE = 12;

// Policy Status Options
export const POLICY_STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  { value: 'uploaded', label: 'Uploaded' },
  { value: 'processing', label: 'Processing' },
  { value: 'analyzed', label: 'Analyzed' },
  { value: 'failed', label: 'Failed' },
  { value: 'archived', label: 'Archived' },
];

// Policy Type Options
export const POLICY_TYPE_OPTIONS = [
  { value: '', label: 'All Types' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'education', label: 'Education' },
  { value: 'agriculture', label: 'Agriculture' },
  { value: 'employment', label: 'Employment' },
  { value: 'housing', label: 'Housing' },
  { value: 'social_welfare', label: 'Social Welfare' },
  { value: 'infrastructure', label: 'Infrastructure' },
  { value: 'environment', label: 'Environment' },
  { value: 'finance', label: 'Finance' },
  { value: 'other', label: 'Other' },
];

// Error Messages
export const ERROR_FILE_TOO_LARGE = `File size must be less than ${MAX_FILE_SIZE_MB}MB`;
export const ERROR_INVALID_FILE_TYPE = 'Please select a PDF file';
export const ERROR_UPLOAD_FAILED = 'Failed to upload file';
export const ERROR_NETWORK = 'Network error. Please check your connection';
export const ERROR_SERVER = 'Server error. Please try again later';

// Success Messages
export const SUCCESS_UPLOAD = 'File uploaded successfully';
export const SUCCESS_DELETE = 'Policy deleted successfully';

// UI Text
export const APP_NAME = 'CivicLens AI';
export const APP_TAGLINE = 'AI-powered platform to translate government policies into personalized, multilingual guidance for every citizen.';

// Date/Time Formats
export const DATE_FORMAT = 'MMM DD, YYYY';
export const DATETIME_FORMAT = 'MMM DD, YYYY HH:mm';
