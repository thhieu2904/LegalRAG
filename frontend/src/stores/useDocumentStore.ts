import { create } from 'zustand';
import { apiClient } from '@/services/api/client';
import { ENDPOINTS } from '@/services/api/endpoints';
import type {
  Document,
  ListDocumentsResponse,
  DocumentDetailResponse,
} from '../types/document.types';

interface DocumentStore {
  documents: Document[];
  loading: boolean;
  error: string | null;
  totalCount: number;

  // Fetch documents (with optional filters)
  fetchDocuments: (collectionId?: string, limit?: number, offset?: number) => Promise<void>;

  // Upload document
  uploadDocument: (collectionId: string, title: string, file: File) => Promise<void>;

  // Update document title
  updateDocument: (id: string, title: string) => Promise<void>;

  // Delete document
  deleteDocument: (id: string) => Promise<void>;

  // Get document details
  getDocumentDetail: (id: string) => Promise<DocumentDetailResponse>;

  // Clear error
  clearError: () => void;
}

export const useDocumentStore = create<DocumentStore>((set, get) => ({
  documents: [],
  loading: false,
  error: null,
  totalCount: 0,

  fetchDocuments: async (collectionId?: string, limit = 100, offset = 0) => {
    set({ loading: true, error: null });
    try {
      const params: Record<string, string | number> = {
        limit,
        offset,
      };

      if (collectionId) {
        params.collection_id = collectionId;
      }

      const response = await apiClient.get<ListDocumentsResponse>(ENDPOINTS.ADMIN.DOCUMENTS, {
        params,
      });

      set({
        documents: response.data.documents,
        totalCount: response.data.total,
        loading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch documents',
        loading: false,
      });
    }
  },

  uploadDocument: async (collectionId: string, title: string, file: File) => {
    set({ loading: true, error: null });
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('collection_id', collectionId);
      formData.append('title', title);

      await apiClient.post(ENDPOINTS.ADMIN.DOCUMENTS, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Refresh documents list
      await get().fetchDocuments(collectionId);

      set({ loading: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to upload document',
        loading: false,
      });
      throw error; // Re-throw to handle in UI
    }
  },

  updateDocument: async (id: string, title: string) => {
    set({ loading: true, error: null });
    try {
      await apiClient.patch(ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id), { title });

      // Update local state
      set((state) => ({
        documents: state.documents.map((doc) => (doc.id === id ? { ...doc, title } : doc)),
        loading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to update document',
        loading: false,
      });
      throw error;
    }
  },

  deleteDocument: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await apiClient.delete(ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id));

      // Remove from local state
      set((state) => ({
        documents: state.documents.filter((doc) => doc.id !== id),
        totalCount: state.totalCount - 1,
        loading: false,
      }));
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete document',
        loading: false,
      });
      throw error;
    }
  },

  getDocumentDetail: async (id: string): Promise<DocumentDetailResponse> => {
    set({ loading: true, error: null });
    try {
      const response = await apiClient.get<DocumentDetailResponse>(
        ENDPOINTS.ADMIN.DOCUMENT_BY_ID(id)
      );

      set({ loading: false });
      return response.data;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch document details',
        loading: false,
      });
      throw error;
    }
  },

  clearError: () => set({ error: null }),
}));
