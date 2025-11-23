/**
 * Axios Client Configuration
 */

import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { API_BASE_URL, API_TIMEOUT, API_HEADERS } from '@/constants';
import { getAuthToken } from '@/stores/authStore';

/**
 * Query Service Base URL (separate from admin service)
 */
const QUERY_SERVICE_URL = import.meta.env.VITE_QUERY_SERVICE_URL || 'http://localhost:8002';

/**
 * Create Axios instance for Admin Service
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: API_HEADERS,
});

/**
 * Create Axios instance for Query Service (no auth needed for public queries)
 */
export const queryClient: AxiosInstance = axios.create({
  baseURL: QUERY_SERVICE_URL,
  timeout: 60000, // Longer timeout for LLM responses
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor - Inject JWT token
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get token from auth store
    const token = getAuthToken();

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
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

          // Clear localStorage
          localStorage.removeItem('auth-storage');

          // Redirect to login (if not already there)
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
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
