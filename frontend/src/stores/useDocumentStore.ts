import { create } from 'zustand';
import type {
  Document,
  ListDocumentsResponse,
  DocumentDetailResponse,
} from '../types/document.types';

const API_BASE_URL = 'http://localhost:8001';

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
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });

      if (collectionId) {
        params.append('collection_id', collectionId);
      }

      const response = await fetch(`${API_BASE_URL}/admin/documents?${params}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.statusText}`);
      }

      const data: ListDocumentsResponse = await response.json();

      set({
        documents: data.documents,
        totalCount: data.total,
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

      const response = await fetch(`${API_BASE_URL}/admin/process-document`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to upload document');
      }

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
      const response = await fetch(`${API_BASE_URL}/admin/documents/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });

      if (!response.ok) {
        throw new Error('Failed to update document');
      }

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
      const response = await fetch(`${API_BASE_URL}/admin/documents/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete document');
      }

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
      const response = await fetch(`${API_BASE_URL}/admin/documents/${id}`);

      if (!response.ok) {
        throw new Error('Failed to fetch document details');
      }

      const data = await response.json();
      set({ loading: false });
      return data;
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
