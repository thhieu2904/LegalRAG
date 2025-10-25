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

// ========== QUESTIONS CRUD OPERATIONS ==========

/**
 * ✏️ UPDATE QUESTIONS
 * Cập nhật questions cho một document
 */
export const updateQuestions = async (
  collectionName: string,
  docId: string,
  mainQuestion: string,
  questionVariants: string[],
  triggerRebuild: boolean = false
): Promise<{
  update_result: {
    success: boolean;
    backup_path: string;
  };
  rebuild_status?: {
    triggered: boolean;
    pid?: number;
    message?: string;
  };
}> => {
  try {
    console.log(
      `✏️ Updating questions for ${collectionName}/${docId} (rebuild=${triggerRebuild})`
    );

    const response = await adminAPI.put<
      AdminApiResponse<{
        update_result: {
          success: boolean;
          backup_path: string;
        };
        rebuild_status?: {
          triggered: boolean;
          pid?: number;
          message?: string;
        };
      }>
    >(
      `/api/questions/collections/${collectionName}/documents/${docId}?rebuild=${triggerRebuild}`,
      {
        main_question: mainQuestion,
        question_variants: questionVariants,
      }
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to update questions");
    }

    console.log(`✅ Questions updated for ${docId}`);
    if (response.data.data.rebuild_status?.triggered) {
      console.log(
        `🚀 Rebuild triggered: PID ${response.data.data.rebuild_status.pid}`
      );
    }

    return response.data.data;
  } catch (error) {
    console.error(
      `❌ Error updating questions for ${collectionName}/${docId}:`,
      error
    );
    throw error;
  }
};

/**
 * 🔄 UPDATE VARIANTS ONLY
 * Cập nhật chỉ question variants (giữ nguyên main question)
 */
export const updateVariants = async (
  collectionName: string,
  docId: string,
  questionVariants: string[],
  triggerRebuild: boolean = false
): Promise<{
  update_result: {
    success: boolean;
    backup_path: string;
  };
  rebuild_status?: {
    triggered: boolean;
    pid?: number;
  };
}> => {
  try {
    console.log(
      `🔄 Updating variants for ${collectionName}/${docId} (${questionVariants.length} variants)`
    );

    const response = await adminAPI.patch<
      AdminApiResponse<{
        update_result: {
          success: boolean;
          backup_path: string;
        };
        rebuild_status?: {
          triggered: boolean;
          pid?: number;
        };
      }>
    >(
      `/api/questions/collections/${collectionName}/documents/${docId}/variants?rebuild=${triggerRebuild}`,
      {
        question_variants: questionVariants,
      }
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to update variants");
    }

    console.log(`✅ Variants updated for ${docId}`);
    return response.data.data;
  } catch (error) {
    console.error(
      `❌ Error updating variants for ${collectionName}/${docId}:`,
      error
    );
    throw error;
  }
};

/**
 * 🗑️ DELETE QUESTIONS
 * Xóa questions file của một document
 */
export const deleteQuestions = async (
  collectionName: string,
  docId: string,
  triggerRebuild: boolean = false
): Promise<{
  delete_result: {
    success: boolean;
    backup_path: string;
  };
  rebuild_status?: {
    triggered: boolean;
    pid?: number;
  };
}> => {
  try {
    console.log(
      `🗑️ Deleting questions for ${collectionName}/${docId} (rebuild=${triggerRebuild})`
    );

    const response = await adminAPI.delete<
      AdminApiResponse<{
        delete_result: {
          success: boolean;
          backup_path: string;
        };
        rebuild_status?: {
          triggered: boolean;
          pid?: number;
        };
      }>
    >(
      `/api/questions/collections/${collectionName}/documents/${docId}?rebuild=${triggerRebuild}`
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to delete questions");
    }

    console.log(`✅ Questions deleted for ${docId}`);
    return response.data.data;
  } catch (error) {
    console.error(
      `❌ Error deleting questions for ${collectionName}/${docId}:`,
      error
    );
    throw error;
  }
};

// ========== REBUILD MANAGEMENT ==========

/**
 * 🚀 TRIGGER REBUILD
 * Kích hoạt rebuild VectorDB
 */
export const triggerRebuild = async (
  scope: "document" | "collection" | "all",
  collection?: string,
  docId?: string
): Promise<{
  success: boolean;
  pid: number;
  message: string;
}> => {
  try {
    console.log(
      `🚀 Triggering rebuild: scope=${scope}, collection=${collection}, doc=${docId}`
    );

    const params = new URLSearchParams();
    params.append("scope", scope);
    if (collection) params.append("collection", collection);
    if (docId) params.append("doc_id", docId);

    const response = await adminAPI.post<
      AdminApiResponse<{
        success: boolean;
        pid: number;
        message: string;
      }>
    >(`/api/questions/rebuild/trigger?${params.toString()}`);

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to trigger rebuild");
    }

    console.log(`✅ Rebuild triggered: PID ${response.data.data.pid}`);
    return response.data.data;
  } catch (error) {
    console.error("❌ Error triggering rebuild:", error);
    throw error;
  }
};

/**
 * 📊 GET REBUILD STATUS
 * Lấy trạng thái rebuild hiện tại
 */
export const getRebuildStatus = async (): Promise<{
  status: "idle" | "queued" | "running" | "success" | "failed";
  progress: number;
  message?: string;
  pid?: number;
  error?: string;
}> => {
  try {
    const response = await adminAPI.get<
      AdminApiResponse<{
        status: "idle" | "queued" | "running" | "success" | "failed";
        progress: number;
        message?: string;
        pid?: number;
        error?: string;
      }>
    >("/api/questions/rebuild/status");

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to get rebuild status");
    }

    return response.data.data;
  } catch (error) {
    console.error("❌ Error getting rebuild status:", error);
    throw error;
  }
};

/**
 * ⛔ CANCEL REBUILD
 * Hủy quá trình rebuild đang chạy
 */
export const cancelRebuild = async (): Promise<{
  success: boolean;
  message: string;
}> => {
  try {
    console.log("⛔ Canceling rebuild...");

    const response = await adminAPI.post<
      AdminApiResponse<{
        success: boolean;
        message: string;
      }>
    >("/api/questions/rebuild/cancel");

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to cancel rebuild");
    }

    console.log("✅ Rebuild canceled");
    return response.data.data;
  } catch (error) {
    console.error("❌ Error canceling rebuild:", error);
    throw error;
  }
};

/**
 * 📦 STORAGE MANAGEMENT TYPES
 */
export interface StoredFormInfo {
  form_id: number;
  scan_cccd: string;
  scan_ho_ten: string;
  filename: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  form_path?: string;
}

export interface StoredCCCDInfo {
  scan_cccd: string;
  scan_ho_ten: string;
  form_count: number;
  total_size_mb: number;
}

export interface StorageStats {
  total_forms: number;
  total_users: number;
  total_size_mb: number;
  cccd_list: StoredCCCDInfo[];
}

/**
 * 📊 GET STORAGE STATISTICS
 * Lấy thống kê lưu trữ form
 */
export const fetchStorageStats = async (): Promise<StorageStats> => {
  try {
    console.log("📊 Fetching storage statistics...");

    const response = await adminAPI.get<AdminApiResponse<StorageStats>>(
      "/api/v1/storage/stats"
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch storage stats");
    }

    console.log(`✅ Storage stats: ${response.data.data.total_forms} forms`);
    return response.data.data;
  } catch (error) {
    console.error("❌ Error fetching storage stats:", error);
    throw error;
  }
};

/**
 * 👥 GET ALL STORED USERS
 * Lấy danh sách tất cả users có form lưu
 */
export const fetchAllStoredUsers = async (): Promise<StorageStats> => {
  try {
    console.log("👥 Fetching all stored users...");

    const response = await adminAPI.get<AdminApiResponse<StorageStats>>(
      "/api/v1/storage/list"
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch users");
    }

    console.log(`✅ Loaded ${response.data.data.cccd_list.length} users`);
    return response.data.data;
  } catch (error) {
    console.error("❌ Error fetching stored users:", error);
    throw error;
  }
};

/**
 * 📋 GET FORMS BY CCCD
 * Lấy danh sách form của một user (theo CCCD)
 */
export const fetchFormsByCCCD = async (
  cccd: string
): Promise<StoredFormInfo[]> => {
  try {
    console.log(`📋 Fetching forms for CCCD: ${cccd}`);

    const response = await adminAPI.get<AdminApiResponse<StoredFormInfo[]>>(
      "/api/v1/storage/list",
      {
        params: { cccd },
      }
    );

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to fetch forms");
    }

    console.log(`✅ Loaded ${response.data.data.length} forms for ${cccd}`);
    return response.data.data;
  } catch (error) {
    console.error(`❌ Error fetching forms for ${cccd}:`, error);
    throw error;
  }
};

/**
 * 📥 DOWNLOAD STORED FORM
 * Tải xuống file form đã lưu
 */
export const downloadStoredForm = async (
  formId: number,
  filename: string
): Promise<void> => {
  try {
    console.log(`📥 Downloading form: ${filename}`);

    const response = await adminAPI.get(`/api/v1/storage/download/${formId}`, {
      responseType: "blob",
    });

    // Tạo link download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);

    console.log(`✅ Form downloaded: ${filename}`);
  } catch (error) {
    console.error(`❌ Error downloading form:`, error);
    throw error;
  }
};

/**
 * 🗑️ DELETE STORED FORM
 * Xóa form đã lưu (từ database và disk)
 */
export const deleteStoredForm = async (
  formId: number
): Promise<{
  status: string;
  message: string;
  form_id: number;
  filename: string;
}> => {
  try {
    console.log(`🗑️ Deleting form: ${formId}`);

    const response = await adminAPI.delete<
      AdminApiResponse<{
        status: string;
        message: string;
        form_id: number;
        filename: string;
      }>
    >(`/api/v1/storage/delete/${formId}`);

    if (!response.data.success) {
      throw new Error(response.data.message || "Failed to delete form");
    }

    console.log(`✅ Form deleted: ${response.data.data.filename}`);
    return response.data.data;
  } catch (error) {
    console.error("❌ Error deleting form:", error);
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
  // CRUD operations
  updateQuestions,
  updateVariants,
  deleteQuestions,
  // Rebuild management
  triggerRebuild,
  getRebuildStatus,
  cancelRebuild,
  // Storage management
  fetchStorageStats,
  fetchAllStoredUsers,
  fetchFormsByCCCD,
  downloadStoredForm,
  deleteStoredForm,
};
