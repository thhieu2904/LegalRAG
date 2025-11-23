/**
 * Auth Store - Zustand State Management
 * Manages authentication state, JWT token, and user information
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { API_BASE_URL } from '../constants/api.constants';

/**
 * Role Interface - matches backend RoleResponse
 */
export interface Role {
  id: number;
  code: 'giao_vien' | 'sinh_vien' | 'admin';
  name: string;
}

/**
 * User Interface - matches backend UserResponse
 * Simple user model from auth-service
 */
export interface User {
  id: string;
  username: string;
  email?: string;
  role: Role; // Role object with id, code, name
  is_active: boolean;
  email_verified?: boolean;
  last_login_at?: string;
  created_at: string;
}

/**
 * GiaoVienInfo - Teacher profile details
 */
export interface GiaoVienInfo {
  ma_giao_vien: string;
  ten_giao_vien: string;
  email: string;
  ma_chuyen_nganh: string;
  chuc_vu?: string;
  is_active: boolean;
}

/**
 * SinhVienInfo - Student profile details
 */
export interface SinhVienInfo {
  ma_sinh_vien: string;
  ten_sinh_vien: string;
  email: string;
  ma_chuyen_nganh: string;
  khoa_hoc: number;
  is_active: boolean;
}

/**
 * UserProfileResponse - Full profile from /auth/me/profile
 */
export interface UserProfileResponse {
  user: User;
  giao_vien?: GiaoVienInfo;
  sinh_vien?: SinhVienInfo;
}

/**
 * Login Response from auth-service
 */
interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

/**
 * Auth State Interface
 */
interface AuthState {
  // State
  user: User | null;
  token: string | null;
  profile: GiaoVienInfo | SinhVienInfo | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (username: string, password: string) => Promise<LoginResponse>;
  logout: () => void;
  fetchProfile: () => Promise<void>;
  setError: (error: string | null) => void;
  clearError: () => void;
}

/**
 * Auth Store - with localStorage persistence
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      token: null,
      profile: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /**
       * Login - Call auth-service via Kong Gateway
       */
      login: async (username: string, password: string): Promise<LoginResponse> => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
          });

          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Đăng nhập thất bại');
          }

          const data: LoginResponse = await response.json();

          // Update state
          set({
            user: data.user,
            token: data.access_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          return data;
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : 'Đăng nhập thất bại';
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: errorMessage,
          });
          throw error;
        }
      },

      /**
       * Fetch user profile - Call /auth/me/profile
       */
      fetchProfile: async () => {
        const { token } = get();

        if (!token) {
          console.error('No token available for fetching profile');
          return;
        }

        try {
          const response = await fetch(`${API_BASE_URL}/auth/me/profile`, {
            method: 'GET',
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error('Failed to fetch profile');
          }

          const data: UserProfileResponse = await response.json();

          // Extract profile based on role
          const profile = data.giao_vien || data.sinh_vien || null;

          set({ profile });
        } catch (error) {
          console.error('Failed to fetch profile:', error);
        }
      },

      /**
       * Logout - Clear all auth state
       */
      logout: () => {
        set({
          user: null,
          token: null,
          profile: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
        // Clear localStorage
        localStorage.removeItem('auth-storage');
      },

      /**
       * Set error message
       */
      setError: (error: string | null) => {
        set({ error });
      },

      /**
       * Clear error message
       */
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        // Only persist these fields
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

/**
 * Helper: Get current token (for API calls)
 */
export const getAuthToken = (): string | null => {
  return useAuthStore.getState().token;
};

/**
 * Helper: Get current user
 */
export const getCurrentUser = (): User | null => {
  return useAuthStore.getState().user;
};

/**
 * Helper: Check if user has specific role
 */
export const hasRole = (role: 'giao_vien' | 'sinh_vien' | 'admin'): boolean => {
  const user = useAuthStore.getState().user;
  return user?.role?.code === role;
};
