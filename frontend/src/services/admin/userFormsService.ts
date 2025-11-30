/**
 * User Forms Service - API calls for admin management of user-filled forms
 */

import { apiClient } from '../api/client';
import { ENDPOINTS } from '../api/endpoints';
import type { UserFormListResponse, UserFormDeleteResponse } from '@/types/userForms.types';

/**
 * Get all user-filled forms
 * @param sessionId - Optional filter by session ID
 */
export const getUserForms = async (sessionId?: string): Promise<UserFormListResponse> => {
  const url = sessionId
    ? ENDPOINTS.ADMIN.USER_FORMS_BY_SESSION(sessionId)
    : ENDPOINTS.ADMIN.USER_FORMS;

  const response = await apiClient.get<UserFormListResponse>(url);
  return response.data;
};

/**
 * Download a user-filled form
 * @param sessionId - Session ID
 * @param filename - Filename to download
 */
export const downloadUserForm = async (sessionId: string, filename: string): Promise<Blob> => {
  const url = `${ENDPOINTS.ADMIN.USER_FORMS}/${sessionId}/download/${filename}`;
  const response = await apiClient.get(url, { responseType: 'blob' });
  return response.data;
};

/**
 * Delete a specific user-filled form
 * @param sessionId - Session ID
 * @param filename - Filename to delete
 */
export const deleteUserForm = async (
  sessionId: string,
  filename: string
): Promise<UserFormDeleteResponse> => {
  const url = ENDPOINTS.ADMIN.DELETE_USER_FORM(sessionId, filename);
  const response = await apiClient.delete<UserFormDeleteResponse>(url);
  return response.data;
};

/**
 * Delete all forms for a session
 * @param sessionId - Session ID to delete all forms for
 */
export const deleteSessionForms = async (sessionId: string): Promise<UserFormDeleteResponse> => {
  const url = ENDPOINTS.ADMIN.USER_FORMS_BY_SESSION(sessionId);
  const response = await apiClient.delete<UserFormDeleteResponse>(url);
  return response.data;
};

export const userFormsService = {
  getUserForms,
  downloadUserForm,
  deleteUserForm,
  deleteSessionForms,
};
