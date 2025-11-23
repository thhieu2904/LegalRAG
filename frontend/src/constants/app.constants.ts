/**
 * Application Configuration Constants
 */

export const APP_TITLE = import.meta.env.VITE_APP_TITLE || 'AI Center RAG';

/**
 * File Upload Configuration
 */
export const MAX_FILE_SIZE = Number(import.meta.env.VITE_MAX_FILE_SIZE) || 10485760; // 10MB
export const ALLOWED_FILE_TYPES = ['application/pdf', 'application/msword', 'text/plain'];
export const ALLOWED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt'];

/**
 * Chat Configuration
 */
export const DEFAULT_TOP_K = 5;
export const DEFAULT_THRESHOLD = 0.7;
export const MAX_MESSAGE_LENGTH = 1000;
export const CHAT_STORAGE_KEY = 'aicenter-chat-history';

/**
 * Upload Configuration
 */
export const UPLOAD_STORAGE_KEY = 'aicenter-upload-history';
export const MAX_UPLOAD_HISTORY = 50;

/**
 * Pagination
 */
export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

/**
 * Metadata Options
 */
export const MA_KHOA_OPTIONS = [
  { value: 'CNTT', label: 'Công Nghệ Thông Tin' },
  { value: 'KTPM', label: 'Kỹ Thuật Phần Mềm' },
  { value: 'KHMT', label: 'Khoa Học Máy Tính' },
];

export const NAM_HOC_OPTIONS = [
  { value: 1, label: 'Năm 1' },
  { value: 2, label: 'Năm 2' },
  { value: 3, label: 'Năm 3' },
  { value: 4, label: 'Năm 4' },
];

export const HOC_KY_OPTIONS = [
  { value: 1, label: 'Học kỳ 1' },
  { value: 2, label: 'Học kỳ 2' },
  { value: 3, label: 'Học kỳ Hè' },
];

export const MON_HOC_OPTIONS = [
  { value: 'CSC101', label: 'Lập trình căn bản' },
  { value: 'CSC102', label: 'Cấu trúc dữ liệu' },
  { value: 'CSC201', label: 'Cơ sở dữ liệu' },
  { value: 'CSC202', label: 'Mạng máy tính' },
  { value: 'CSC301', label: 'Trí tuệ nhân tạo' },
  { value: 'CSC302', label: 'Học máy' },
];

export const LOAI_NOI_DUNG_OPTIONS = [
  { value: 'lecture', label: 'Bài giảng' },
  { value: 'exam', label: 'Đề thi' },
  { value: 'exercise', label: 'Bài tập' },
  { value: 'reference', label: 'Tài liệu tham khảo' },
];

/**
 * Response Status
 */
export const RESPONSE_STATUS = {
  SUCCESS: 'success',
  ERROR: 'error',
  LOADING: 'loading',
} as const;

/**
 * Message Roles
 */
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
} as const;
