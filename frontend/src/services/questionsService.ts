/**
 * Service for managing router questions API calls
 */

const API_BASE_URL = "/router";

export interface Collection {
  name: string;
  display_name: string;
  total_questions: number;
  active_questions: number;
}

export interface Document {
  id: string;
  title: string;
  collection: string;
  path: string;
  question_count: number;
  json_file: string;
}

export interface Question {
  id: string;
  text: string;
  collection: string;
  keywords: string[];
  type: string;
  category: string;
  priority_score: number;
  status: string;
  created_at?: string;
  updated_at?: string;
  source?: string;
}

export interface QuestionCreate {
  text: string;
  keywords?: string[];
  type?: string;
  category?: string;
  priority_score?: number;
}

export interface QuestionUpdate {
  text?: string;
  keywords?: string[];
  category?: string;
  priority_score?: number;
  status?: string;
}

export interface QuestionSearchResult extends Question {
  similarity_score: number;
}

export interface ApiResponse {
  success: boolean;
  message: string;
  question_id?: string;
  collection?: string;
  updates?: Record<string, unknown>;
}

class QuestionsService {
  private async fetchApi(url: string, options: RequestInit = {}) {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Collections
  async getCollections(): Promise<Collection[]> {
    return this.fetchApi(`${API_BASE_URL}/collections`);
  }

  // Documents
  async getCollectionDocuments(collectionName: string): Promise<Document[]> {
    return this.fetchApi(
      `${API_BASE_URL}/collections/${collectionName}/documents`
    );
  }

  async getDocumentQuestions(
    collectionName: string,
    documentId: string,
    includeDeleted: boolean = false
  ): Promise<Question[]> {
    const params = new URLSearchParams({
      include_deleted: includeDeleted.toString(),
    });
    return this.fetchApi(
      `${API_BASE_URL}/router/collections/${collectionName}/documents/${documentId}/questions?${params}`
    );
  }

  async getCollectionQuestions(
    collectionName: string,
    includeDeleted: boolean = false
  ): Promise<Question[]> {
    const params = new URLSearchParams({
      include_deleted: includeDeleted.toString(),
    });
    return this.fetchApi(
      `${API_BASE_URL}/router/collections/${collectionName}/questions?${params}`
    );
  }

  // Questions CRUD
  async createQuestion(
    collectionName: string,
    questionData: QuestionCreate
  ): Promise<ApiResponse> {
    return this.fetchApi(
      `${API_BASE_URL}/router/collections/${collectionName}/questions`,
      {
        method: "POST",
        body: JSON.stringify(questionData),
      }
    );
  }

  async updateQuestion(
    collectionName: string,
    questionId: string,
    updates: QuestionUpdate
  ): Promise<ApiResponse> {
    return this.fetchApi(
      `${API_BASE_URL}/router/collections/${collectionName}/questions/${questionId}`,
      {
        method: "PUT",
        body: JSON.stringify(updates),
      }
    );
  }

  async deleteQuestion(
    collectionName: string,
    questionId: string
  ): Promise<ApiResponse> {
    return this.fetchApi(
      `${API_BASE_URL}/router/collections/${collectionName}/questions/${questionId}`,
      {
        method: "DELETE",
      }
    );
  }

  // Search
  async searchQuestions(
    query: string,
    collection?: string,
    limit: number = 10
  ): Promise<QuestionSearchResult[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });
    if (collection) {
      params.append("collection", collection);
    }
    return this.fetchApi(`${API_BASE_URL}/search?${params}`);
  }

  // Utility
  async saveCollectionToFile(collectionName: string): Promise<ApiResponse> {
    return this.fetchApi(`${API_BASE_URL}/collections/${collectionName}/save`, {
      method: "POST",
    });
  }
}

export const questionsService = new QuestionsService();
