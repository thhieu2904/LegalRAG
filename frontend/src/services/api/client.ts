/**
 * Axios Client Configuration
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { API_TIMEOUT, API_HEADERS } from '@/constants';

/**
 * Admin Service Base URL
 */
const ADMIN_SERVICE_URL = import.meta.env.VITE_ADMIN_SERVICE_URL || 'http://localhost:8001';

/**
 * Query Service Base URL (separate from admin service)
 */
const QUERY_SERVICE_URL = import.meta.env.VITE_QUERY_SERVICE_URL || 'http://localhost:8002';

/**
 * Form Service Base URL (accessed via query-service /forms/*)
 */
export const FORM_SERVICE_URL = import.meta.env.VITE_FORM_SERVICE_URL || 'http://localhost:8015';

/**
 * Storage Service Base URL (for file downloads)
 */
export const STORAGE_SERVICE_URL =
  import.meta.env.VITE_STORAGE_SERVICE_URL || 'http://localhost:8010';

/**
 * Create Axios instance for Admin Service
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: ADMIN_SERVICE_URL,
  timeout: API_TIMEOUT,
  headers: API_HEADERS,
});

/**
 * Create Axios instance for Query Service (no auth needed for public queries)
 */
export const queryClient: AxiosInstance = axios.create({
  baseURL: QUERY_SERVICE_URL,
  timeout: 180000, // 3 minutes for complex reranking + LLM generation
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Create Axios instance for Form Service (via query-service gateway)
 */
export const formClient: AxiosInstance = axios.create({
  baseURL: QUERY_SERVICE_URL,
  timeout: 60000, // 1 minute for form operations
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor - Inject JWT token for admin requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get admin token from localStorage
    const adminToken = localStorage.getItem('admin_token');

    // Add token to admin requests
    if (adminToken && config.headers && config.url?.startsWith('/admin')) {
      config.headers.Authorization = `Bearer ${adminToken}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor - Handle errors and auth expiration
 */
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;

      switch (status) {
        case 401: {
          console.error('Unauthorized - Token expired or invalid');

          // Clear admin token
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_token_expires');

          // Redirect to admin login if on admin page
          if (window.location.pathname.startsWith('/admin')) {
            window.location.href = '/admin/login';
          }
          break;
        }
        case 403:
          console.error('Forbidden - Access denied');
          break;
        case 404:
          console.error('Not Found - Resource not found');
          break;
        case 500:
          console.error('Internal Server Error');
          break;
        default:
          console.error(`Error ${status}: ${error.message}`);
      }
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error - No response from server');
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }

    return Promise.reject(error);
  }
);
