import axios from "axios";
import type { ChatRequest, ChatResponse } from "../types/chat";

const API_BASE_URL = "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

interface ClarificationOption {
  id: string;
  title: string;
  description: string;
  confidence?: string;
  examples?: string[];
  action: string;
  collection?: string;
  question_text?: string;
  category?: string;
}

export const apiService = {
  async sendQuery(query: string, sessionId: string | null) {
    const response = await api.post("/query", {
      query,
      session_id: sessionId,
    });
    return response.data;
  },

  async sendClarificationResponse(
    sessionId: string,
    originalQuery: string,
    selectedOption: ClarificationOption
  ) {
    const response = await api.post("/clarify", {
      session_id: sessionId,
      original_query: originalQuery,
      selected_option: selectedOption,
    });
    return response.data;
  },

  async checkHealth(): Promise<any> {
    const response = await api.get("/health");
    return response.data;
  },

  async createSession(): Promise<{ session_id: string }> {
    const response = await api.post("/session/create");
    return response.data;
  },

  async getSessionInfo(sessionId: string): Promise<{
    session_id: string;
    created_at: string;
    query_count: number;
    last_query_at?: string;
  }> {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  },
};

export const chatApi = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post("/query", request);
    return response.data;
  },

  async checkHealth(): Promise<any> {
    const response = await api.get("/health");
    return response.data;
  },

  async createSession(): Promise<{ session_id: string }> {
    const response = await api.post("/session/create");
    return response.data;
  },

  async getSessionInfo(sessionId: string): Promise<{
    session_id: string;
    created_at: string;
    query_count: number;
    last_query_at?: string;
  }> {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  },
};

export default api;
