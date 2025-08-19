import axios from "axios";

// Get base URL from environment or default to localhost
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface ChatRequest {
  query: string;
  session_id?: string | null;
  forced_collection?: string;
}

export interface ClarificationOption {
  id: string;
  title: string;
  description: string;
  confidence?: string;
  examples?: string[];
  action: string;
  collection?: string;
  question_text?: string;
  document_title?: string; // 🔥 NEW: For exact document filtering
  source_file?: string; // 🔥 NEW: Full source path
  similarity?: number; // 🔥 NEW: Similarity score
  category?: string;
}

export interface ClarificationData {
  message: string;
  options: ClarificationOption[];
  style: string;
  stage?: number;
  collection?: string;
  original_query?: string;
}

export interface ContextInfo {
  nucleus_chunks: number;
  context_length: number;
  source_collections: string[];
  source_documents: string[];
}

// 🔥 NEW: Context Summary interface
export interface ContextSummary {
  session_id: string;
  has_active_context: boolean;
  current_collection: string | null;
  current_collection_display: string | null;
  preserved_document: string | null;
  active_filters: Record<string, unknown>;
  confidence_level: number;
  context_age_minutes: number;
  query_count: number;
  last_activity: number;
}

// 🔥 NEW: Session info interface
export interface SessionInfo {
  session_id: string;
  created_at: number;
  last_accessed: number;
  query_count: number;
  metadata: Record<string, unknown>;
  context_summary: ContextSummary;
}

export interface ApiResponse {
  type: string;
  answer?: string;
  clarification?: ClarificationData;
  session_id: string;
  processing_time: number;
  context_info?: ContextInfo;
  error?: string;
}

export interface ChatResponse {
  response: string;
  session_id?: string;
  confidence?: number;
  sources?: string[];
  processing_time?: number;
  is_ambiguous?: boolean;
  clarifying_questions?: string[];
  metadata?: {
    confidence?: number;
    sources?: string[];
    processing_time?: number;
  };
  apiResponse?: ApiResponse; // Store full API response
}

export class ChatService {
  private static sessionId: string | null = null;

  static async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const requestData: ChatRequest = {
        query: message,
        session_id: this.sessionId || null, // Use null instead of undefined for consistency
      };

      const response = await axios.post<ApiResponse>(
        `${BASE_URL}/api/v2/optimized-query`,
        requestData,
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 60000, // Increase timeout to 60 seconds for complex queries
        }
      );

      const apiResponse = response.data;

      // Store session ID for subsequent requests
      if (apiResponse.session_id) {
        this.sessionId = apiResponse.session_id;
      }

      // Transform API response to ChatResponse format
      return {
        response:
          apiResponse.answer ||
          apiResponse.clarification?.message ||
          "Có lỗi xảy ra",
        session_id: apiResponse.session_id,
        processing_time: apiResponse.processing_time,
        sources: apiResponse.context_info?.source_documents,
        apiResponse: apiResponse, // Store full API response for advanced handling
      };
    } catch (error) {
      console.error("Error sending message to chat API:", error);

      if (axios.isAxiosError(error)) {
        if (error.response?.status === 422) {
          return {
            response:
              "Dữ liệu gửi lên không hợp lệ. Vui lòng thử lại với câu hỏi khác.",
          };
        } else if (error.response?.status === 500) {
          return {
            response: "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau.",
          };
        } else if (error.code === "ECONNABORTED") {
          return {
            response: "Yêu cầu của bạn đã hết thời gian chờ. Vui lòng thử lại.",
          };
        } else if (error.response?.status === 404) {
          return {
            response:
              "Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.",
          };
        }
      }

      return {
        response:
          "Đã có lỗi xảy ra khi xử lý yêu cầu của bạn. Vui lòng thử lại.",
      };
    }
  }

  static async sendClarificationResponse(
    sessionId: string,
    originalQuery: string,
    selectedOption: ClarificationOption
  ): Promise<ChatResponse> {
    try {
      const response = await axios.post<ApiResponse>(
        `${BASE_URL}/api/v2/clarify`,
        {
          session_id: sessionId,
          original_query: originalQuery,
          selected_option: selectedOption,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 60000, // Increase timeout to 60 seconds
        }
      );

      const apiResponse = response.data;

      return {
        response:
          apiResponse.answer ||
          apiResponse.clarification?.message ||
          "Có lỗi xảy ra",
        session_id: apiResponse.session_id,
        processing_time: apiResponse.processing_time,
        sources: apiResponse.context_info?.source_documents,
        apiResponse: apiResponse,
      };
    } catch (error) {
      console.error("Error sending clarification response:", error);
      return { response: "Có lỗi xảy ra khi xử lý lựa chọn của bạn." };
    }
  }

  static resetSession(): void {
    this.sessionId = null;
  }

  static getSessionId(): string | null {
    return this.sessionId;
  }

  // 🔥 NEW: Get session context summary
  static async getSessionContext(
    sessionId: string
  ): Promise<ContextSummary | null> {
    try {
      const response = await axios.get<SessionInfo>(
        `${BASE_URL}/api/v2/session/${sessionId}`,
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 10000,
        }
      );

      return response.data.context_summary;
    } catch (error) {
      console.error("Error getting session context:", error);
      return null;
    }
  }

  // 🔥 NEW: Reset session context
  static async resetSessionContext(sessionId: string): Promise<boolean> {
    try {
      const response = await axios.post(
        `${BASE_URL}/api/v2/session/${sessionId}/reset`,
        {},
        {
          headers: {
            "Content-Type": "application/json",
          },
          timeout: 10000,
        }
      );

      return response.status === 200;
    } catch (error) {
      console.error("Error resetting session context:", error);
      return false;
    }
  }

  // 🔥 NEW: Get current session ID
  static getCurrentSessionId(): string | null {
    return this.sessionId;
  }
}
