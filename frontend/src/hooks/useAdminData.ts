/**
 * 🗃️ ADMIN DATA HOOK
 * Custom hook để quản lý dữ liệu từ admin API
 */

import { useState, useEffect } from "react";
import {
  fetchCollections,
  fetchCollectionDocuments,
  fetchQuestions,
  type AdminCollection,
  type AdminDocument,
  type AdminQuestion,
} from "../api/admin-api";

export interface UseAdminDataResult {
  // Collections
  collections: AdminCollection[];
  isLoadingCollections: boolean;
  collectionsError: string | null;

  // Documents
  documents: AdminDocument[];
  isLoadingDocuments: boolean;
  documentsError: string | null;

  // Questions
  questions: AdminQuestion[];
  isLoadingQuestions: boolean;
  questionsError: string | null;

  // Actions
  loadCollections: () => Promise<void>;
  loadDocuments: (collectionName: string) => Promise<void>;
  loadQuestions: (
    searchQuery?: string,
    collectionFilter?: string
  ) => Promise<void>;
  refreshAll: () => Promise<void>;
}

export const useAdminData = (): UseAdminDataResult => {
  // Collections state
  const [collections, setCollections] = useState<AdminCollection[]>([]);
  const [isLoadingCollections, setIsLoadingCollections] = useState(false);
  const [collectionsError, setCollectionsError] = useState<string | null>(null);

  // Documents state
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false);
  const [documentsError, setDocumentsError] = useState<string | null>(null);

  // Questions state
  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [questionsError, setQuestionsError] = useState<string | null>(null);

  // Load collections
  const loadCollections = async () => {
    try {
      setIsLoadingCollections(true);
      setCollectionsError(null);
      console.log("🗃️ Loading collections from admin API...");

      const collectionsData = await fetchCollections();
      setCollections(collectionsData);

      console.log(`✅ Loaded ${collectionsData.length} collections`);
    } catch (error) {
      console.error("❌ Error loading collections:", error);
      setCollectionsError("Không thể tải danh sách collections");
    } finally {
      setIsLoadingCollections(false);
    }
  };

  // Load documents for a collection
  const loadDocuments = async (collectionName: string) => {
    try {
      setIsLoadingDocuments(true);
      setDocumentsError(null);
      console.log(`🗃️ Loading documents for collection: ${collectionName}`);

      const documentsData = await fetchCollectionDocuments(collectionName);
      setDocuments(documentsData);

      console.log(`✅ Loaded ${documentsData.length} documents`);
    } catch (error) {
      console.error(`❌ Error loading documents for ${collectionName}:`, error);
      setDocumentsError(
        `Không thể tải documents cho collection ${collectionName}`
      );
      setDocuments([]);
    } finally {
      setIsLoadingDocuments(false);
    }
  };

  // Load questions with optional filters
  const loadQuestions = async (
    searchQuery?: string,
    collectionFilter?: string
  ) => {
    try {
      setIsLoadingQuestions(true);
      setQuestionsError(null);
      console.log("🗃️ Loading questions from admin API...");

      const questionsData = await fetchQuestions(searchQuery, collectionFilter);
      setQuestions(questionsData);

      console.log(`✅ Loaded ${questionsData.length} questions`);
    } catch (error) {
      console.error("❌ Error loading questions:", error);
      setQuestionsError("Không thể tải danh sách questions");
    } finally {
      setIsLoadingQuestions(false);
    }
  };

  // Refresh all data
  const refreshAll = async () => {
    await Promise.all([loadCollections(), loadQuestions()]);
  };

  // Auto-load collections on mount
  useEffect(() => {
    loadCollections();
  }, []);

  return {
    // Collections
    collections,
    isLoadingCollections,
    collectionsError,

    // Documents
    documents,
    isLoadingDocuments,
    documentsError,

    // Questions
    questions,
    isLoadingQuestions,
    questionsError,

    // Actions
    loadCollections,
    loadDocuments,
    loadQuestions,
    refreshAll,
  };
};
