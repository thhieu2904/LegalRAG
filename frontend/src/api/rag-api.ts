/**
 * 🤖 RAG SERVICE API - TẤT CẢ CALLS ĐẾN RAG SERVICE (PORT 8000)
 * Chat, Admin, Questions management
 */
import { ragAPI } from "./axios-config";

// ========================================
// CHAT API - Cho ChatPage
// ========================================
export interface ChatMessage {
  message: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  sources?: string[];
  timestamp: string;
}

export const chatAPI = {
  // Gửi tin nhắn chat
  sendMessage: async (message: string): Promise<ChatResponse> => {
    try {
      const response = await ragAPI.post("/chat", { message });
      return response.data;
    } catch (error) {
      console.error("Chat API Error:", error);
      throw error;
    }
  },

  // Lấy lịch sử chat
  getChatHistory: async (): Promise<ChatMessage[]> => {
    try {
      const response = await ragAPI.get("/chat/history");
      return response.data;
    } catch (error) {
      console.error("Chat History API Error:", error);
      throw error;
    }
  },
};

// ========================================
// ADMIN API - Cho AdminPage
// ========================================
export interface SystemStats {
  totalUsers: number;
  totalChats: number;
  systemHealth: string;
  vectordbStatus: string;
}

export interface Collection {
  id: string;
  name: string;
  documentsCount: number;
  createdAt: string;
}

export const adminAPI = {
  // Lấy thống kê hệ thống
  getSystemStats: async (): Promise<SystemStats> => {
    try {
      const response = await ragAPI.get("/admin/stats");
      return response.data;
    } catch (error) {
      console.error("Admin Stats API Error:", error);
      throw error;
    }
  },

  // Quản lý Collections
  getCollections: async (): Promise<Collection[]> => {
    try {
      const response = await ragAPI.get("/admin/collections");
      return response.data;
    } catch (error) {
      console.error("Collections API Error:", error);
      throw error;
    }
  },

  // Xây dựng lại VectorDB
  rebuildVectorDB: async (): Promise<{ message: string }> => {
    try {
      const response = await ragAPI.post("/admin/vectordb/rebuild");
      return response.data;
    } catch (error) {
      console.error("VectorDB Rebuild API Error:", error);
      throw error;
    }
  },

  // Quản lý AI Models
  getModelsStatus: async () => {
    try {
      const response = await ragAPI.get("/admin/models/status");
      return response.data;
    } catch (error) {
      console.error("Models Status API Error:", error);
      throw error;
    }
  },
};

// ========================================
// QUESTIONS API - Cho Admin Questions Management
// ========================================
export interface Question {
  id: string;
  question: string;
  collection: string;
  createdAt: string;
}

export const questionsAPI = {
  // Lấy danh sách questions
  getQuestions: async (): Promise<Question[]> => {
    try {
      const response = await ragAPI.get("/admin/questions");
      return response.data;
    } catch (error) {
      console.error("Questions API Error:", error);
      throw error;
    }
  },

  // Thêm question mới
  addQuestion: async (questionData: {
    question: string;
    collection: string;
  }): Promise<Question> => {
    try {
      const response = await ragAPI.post("/admin/questions", questionData);
      return response.data;
    } catch (error) {
      console.error("Add Question API Error:", error);
      throw error;
    }
  },

  // Cập nhật question
  updateQuestion: async (
    id: string,
    questionData: Partial<Question>
  ): Promise<Question> => {
    try {
      const response = await ragAPI.put(`/admin/questions/${id}`, questionData);
      return response.data;
    } catch (error) {
      console.error("Update Question API Error:", error);
      throw error;
    }
  },

  // Xóa question
  deleteQuestion: async (id: string): Promise<{ message: string }> => {
    try {
      const response = await ragAPI.delete(`/admin/questions/${id}`);
      return response.data;
    } catch (error) {
      console.error("Delete Question API Error:", error);
      throw error;
    }
  },
};
