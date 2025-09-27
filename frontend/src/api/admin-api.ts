/**
 * 🗃️ ADMIN API SERVICE
 * Quản lý collections, documents và questions từ admin service
 */

import { adminAPI } from "./axios-config";
import { formatCollectionName } from "./collection-mapping";

// Types for Admin API
export interface AdminCollection {
  name: string;
  display_name: string;
  document_count: number;
  description: string;
  metadata_exists: boolean;
  error?: string;
}

export interface AdminDocument {
  doc_id: string;
  title: string;
  effective_date: string;
  code: string;
  executing_agency: string;
  source_file: string;
  has_original_doc: boolean;
  has_processed_json: boolean;
  has_questions: boolean;
  question_count: number;
  has_forms: boolean;
  form_count: number;
  applicant_type: string[];
  processing_time_text: string;
  fee_text: string;
  fee_vnd: number;
  status: string;
  error?: string;
}

export interface AdminQuestion {
  id: string;
  main_question: string;
  variants?: string[];
  collection: string;
  doc_id: string;
  category: string;
}

export interface AdminDocumentDetail extends AdminDocument {
  questions?: {
    has_questions: boolean;
    question_count: number;
    questions_preview?: AdminQuestion[];
  };
  forms?: {
    has_forms: boolean;
    form_count: number;
    forms_preview?: string[];
  };
  files?: {
    original_doc?: string;
    processed_json?: string;
    questions_file?: string;
  };
}

export interface AdminHealthStatus {
  status: string;
  service: string;
  environment: string;
  collections_dir: string;
  collections_exist: boolean;
}

export interface AdminApiResponse<T> {
  success: boolean;
  data: T;
  total?: number;
  message?: string;
  error?: string;
}

export interface DashboardAnalytics {
  stats: {
    active_sessions: number;
    total_queries_today: number;
    total_collections: number;
    total_documents: number;
    avg_response_time: number;
  };
  collections_summary: Array<{
    name: string;
    display_name: string;
    document_count: string | number;
  }>;
  system_status: {
    rag_service: string;
    admin_service: string;
    total_collections: number;
    collections_accessible: boolean;
    llm_loaded?: boolean;
    embedding_device?: string;
    router_ready?: boolean;
  };
  timestamp: string;
}

/**
 * 📁 GET ALL COLLECTIONS
 * Lấy danh sách tất cả collections với thông tin metadata
 */
export const fetchCollections = async (): Promise<AdminCollection[]> => {
  try {
    console.log("🗃️ Fetching collections from admin service...");

    const response = await adminAPI.get<AdminApiResponse<AdminCollection[]>>(
      "/api/collections"
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch collections");
    }

    // Enhance với Vietnamese names từ collection-mapping
    const enhancedCollections = response.data.data.map((collection) => ({
      ...collection,
      display_name: formatCollectionName(collection.name), // Override với tên tiếng Việt đúng
    }));

    console.log(`✅ Loaded ${enhancedCollections.length} collections`);
    return enhancedCollections;
  } catch (error) {
    console.error("❌ Error fetching collections:", error);
    throw error;
  }
};

/**
 * 📄 GET COLLECTION DOCUMENTS
 * Lấy danh sách documents trong một collection
 */
export const fetchCollectionDocuments = async (
  collectionName: string
): Promise<AdminDocument[]> => {
  try {
    console.log(`🗃️ Fetching documents for collection: ${collectionName}`);

    const response = await adminAPI.get<AdminApiResponse<AdminDocument[]>>(
      `/api/collections/${collectionName}/documents`
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch documents");
    }

    console.log(
      `✅ Loaded ${response.data.data.length} documents from ${collectionName}`
    );
    return response.data.data;
  } catch (error) {
    console.error(`❌ Error fetching documents for ${collectionName}:`, error);
    throw error;
  }
};

/**
 * 📋 GET DOCUMENT DETAIL
 * Lấy thông tin chi tiết của một document
 */
export const fetchDocumentDetail = async (
  collectionName: string,
  docId: string
): Promise<AdminDocumentDetail> => {
  try {
    console.log(`🗃️ Fetching document detail: ${collectionName}/${docId}`);

    const response = await adminAPI.get<AdminApiResponse<AdminDocumentDetail>>(
      `/api/collections/${collectionName}/documents/${docId}`
    );

    if (!response.data.success) {
      throw new Error(
        response.data.message || "Failed to fetch document detail"
      );
    }

    console.log(`✅ Loaded document detail for ${docId}`);
    return response.data.data;
  } catch (error) {
    console.error(
      `❌ Error fetching document detail ${collectionName}/${docId}:`,
      error
    );
    throw error;
  }
};

/**
 * ❓ GET ALL QUESTIONS
 * Lấy tất cả questions từ tất cả collections với tính năng search
 */
export const fetchQuestions = async (
  searchQuery?: string,
  collectionFilter?: string,
  limit?: number
): Promise<AdminQuestion[]> => {
  try {
    console.log("🗃️ Fetching questions from admin service...");

    const params = new URLSearchParams();
    if (searchQuery) params.append("q", searchQuery);
    if (collectionFilter) params.append("collection", collectionFilter);
    if (limit) params.append("limit", limit.toString());

    const url = `/api/questions${
      params.toString() ? `?${params.toString()}` : ""
    }`;
    const response = await adminAPI.get<AdminApiResponse<AdminQuestion[]>>(url);

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch questions");
    }

    console.log(`✅ Loaded ${response.data.data.length} questions`);
    return response.data.data;
  } catch (error) {
    console.error("❌ Error fetching questions:", error);
    throw error;
  }
};

/**
 * 🔍 SEARCH QUESTIONS
 * Tìm kiếm questions theo từ khóa
 */
export const searchQuestions = async (
  query: string,
  limit = 50
): Promise<AdminQuestion[]> => {
  return fetchQuestions(query, undefined, limit);
};

/**
 * 📊 GET COLLECTION QUESTIONS
 * Lấy questions của một collection cụ thể
 */
export const fetchCollectionQuestions = async (
  collectionName: string
): Promise<AdminQuestion[]> => {
  return fetchQuestions(undefined, collectionName);
};

/**
 * 📋 GET DOCUMENT QUESTIONS
 * Lấy questions của một document cụ thể trong collection
 */
export const fetchDocumentQuestions = async (
  collectionName: string,
  docId: string
): Promise<{
  collection: string;
  doc_id: string;
  document_title: string;
  questions: Array<{
    id: string;
    text: string;
    type: "main" | "variant";
    order: number;
    variant_index?: number;
  }>;
  total: number;
  has_questions: boolean;
}> => {
  try {
    console.log(
      `❓ Fetching questions for document: ${collectionName}/${docId}`
    );

    const response = await adminAPI.get<
      AdminApiResponse<{
        collection: string;
        doc_id: string;
        document_title: string;
        questions: Array<{
          id: string;
          text: string;
          type: "main" | "variant";
          order: number;
          variant_index?: number;
        }>;
        total: number;
        has_questions: boolean;
      }>
    >(`/api/questions/collections/${collectionName}/documents/${docId}`);

    if (!response.data.success) {
      throw new Error(
        response.data.message || "Failed to fetch document questions"
      );
    }

    console.log(`✅ Loaded questions for document ${docId}`);
    return response.data.data;
  } catch (error) {
    console.error(
      `❌ Error fetching questions for ${collectionName}/${docId}:`,
      error
    );
    throw error;
  }
};

/**
 * 🏥 HEALTH CHECK
 * Kiểm tra trạng thái admin service
 */
export const checkAdminHealth = async (): Promise<AdminHealthStatus> => {
  try {
    const response = await adminAPI.get<AdminHealthStatus>("/health");
    return response.data;
  } catch (error) {
    console.error("❌ Admin service health check failed:", error);
    throw error;
  }
};

/**
 * 📊 GET DASHBOARD ANALYTICS
 * Lấy dữ liệu analytics cho dashboard admin
 */
export const fetchDashboardAnalytics =
  async (): Promise<DashboardAnalytics> => {
    try {
      console.log("📊 Fetching dashboard analytics from admin service...");

      const response = await adminAPI.get<AdminApiResponse<DashboardAnalytics>>(
        "/api/analytics/dashboard"
      );

      if (!response.data.success) {
        throw new Error(
          response.data.message || "Failed to fetch dashboard analytics"
        );
      }

      console.log(
        "✅ Dashboard analytics fetched successfully:",
        response.data.data.stats
      );
      return response.data.data;
    } catch (error) {
      console.error("❌ Error fetching dashboard analytics:", error);
      throw error;
    }
  };

export default {
  fetchCollections,
  fetchCollectionDocuments,
  fetchDocumentDetail,
  fetchQuestions,
  searchQuestions,
  fetchCollectionQuestions,
  fetchDocumentQuestions,
  checkAdminHealth,
  fetchDashboardAnalytics,
};
