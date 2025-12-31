/**
 * Admin Store - Collections & Documents Management
 * State management for LegalRAG admin operations
 */

import { create } from 'zustand';
import {
  getCollections,
  createCollection,
  updateCollection,
  deleteCollection,
  getDocuments,
  uploadDocument as uploadDocumentAPI,
} from '@/services/api/admin.service';
import type {
  Collection,
  CreateCollectionRequest,
  UpdateCollectionRequest,
  Document,
} from '@/types/admin.types';

interface AdminState {
  // Collections
  collections: Collection[];
  selectedCollection: Collection | null;
  collectionsLoading: boolean;
  collectionsError: string | null;

  // Documents
  documents: Document[];
  selectedDocument: Document | null;
  documentsLoading: boolean;
  documentsError: string | null;
  documentFilters: {
    collection_id?: string;
    status?: string;
  };

  // Upload
  isUploading: boolean;
  uploadProgress: number;
  uploadError: string | null;
}

interface AdminActions {
  // Collections
  fetchCollections: () => Promise<void>;
  addCollection: (data: CreateCollectionRequest) => Promise<void>;
  editCollection: (id: string, data: UpdateCollectionRequest) => Promise<void>;
  removeCollection: (id: string) => Promise<void>;
  selectCollection: (collection: Collection | null) => void;

  // Documents
  fetchDocuments: (collection_id?: string) => Promise<void>;
  uploadDocument: (file: File, collection_id: string, title: string) => Promise<void>;
  selectDocument: (document: Document | null) => void;
  setDocumentFilters: (filters: { collection_id?: string; status?: string }) => void;

  // State management
  clearErrors: () => void;
  reset: () => void;
}

type AdminStore = AdminState & AdminActions;

const initialState: AdminState = {
  collections: [],
  selectedCollection: null,
  collectionsLoading: false,
  collectionsError: null,
  documents: [],
  selectedDocument: null,
  documentsLoading: false,
  documentsError: null,
  documentFilters: {},
  isUploading: false,
  uploadProgress: 0,
  uploadError: null,
};

export const useAdminStore = create<AdminStore>((set, get) => ({
  ...initialState,

  // ============================================
  // COLLECTIONS ACTIONS
  // ============================================

  fetchCollections: async () => {
    set({ collectionsLoading: true, collectionsError: null });
    try {
      const collections = await getCollections();
      set({ collections, collectionsLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch collections';
      set({ collectionsError: errorMessage, collectionsLoading: false });
      throw error;
    }
  },

  addCollection: async (data: CreateCollectionRequest) => {
    set({ collectionsLoading: true, collectionsError: null });
    try {
      const response = await createCollection(data);
      const { collections } = get();
      set({
        collections: [...collections, response.collection],
        collectionsLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create collection';
      set({ collectionsError: errorMessage, collectionsLoading: false });
      throw error;
    }
  },

  editCollection: async (id: string, data: UpdateCollectionRequest) => {
    set({ collectionsLoading: true, collectionsError: null });
    try {
      const response = await updateCollection(id, data);
      const { collections } = get();
      set({
        collections: collections.map((col) => (col.id === id ? response.collection : col)),
        collectionsLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update collection';
      set({ collectionsError: errorMessage, collectionsLoading: false });
      throw error;
    }
  },

  removeCollection: async (id: string) => {
    set({ collectionsLoading: true, collectionsError: null });
    try {
      await deleteCollection(id);
      const { collections } = get();
      set({
        collections: collections.filter((col) => col.id !== id),
        collectionsLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete collection';
      set({ collectionsError: errorMessage, collectionsLoading: false });
      throw error;
    }
  },

  selectCollection: (collection: Collection | null) => {
    set({ selectedCollection: collection });
  },

  // ============================================
  // DOCUMENTS ACTIONS
  // ============================================

  fetchDocuments: async (collection_id?: string) => {
    set({ documentsLoading: true, documentsError: null });
    try {
      const response = await getDocuments({ collection_id });
      set({ documents: response.documents, documentsLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch documents';
      set({ documentsError: errorMessage, documentsLoading: false });
      throw error;
    }
  },

  uploadDocument: async (file: File, collection_id: string, title: string) => {
    set({ isUploading: true, uploadProgress: 0, uploadError: null });
    try {
      await uploadDocumentAPI(file, collection_id, title);
      set({ isUploading: false, uploadProgress: 100 });
      // Refresh documents list
      await get().fetchDocuments(collection_id);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      set({ uploadError: errorMessage, isUploading: false });
      throw error;
    }
  },

  selectDocument: (document: Document | null) => {
    set({ selectedDocument: document });
  },

  setDocumentFilters: (filters) => {
    set({ documentFilters: filters });
  },

  // ============================================
  // STATE MANAGEMENT
  // ============================================

  clearErrors: () => {
    set({
      collectionsError: null,
      documentsError: null,
      uploadError: null,
    });
  },

  reset: () => {
    set(initialState);
  },
}));
