export interface Message {
  id: string;
  type: "user" | "assistant" | "clarification";
  content: string;
  timestamp: Date;
  sources?: string[];
  source_files?: string[];
  processing_time?: number;
  clarificationOptions?: string[];
  session_id?: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  max_tokens?: number;
  temperature?: number;
  top_k?: number;
}

export interface ClarificationResponse {
  type: "clarification_needed";
  category: string;
  confidence: number;
  clarification: {
    template: string;
    options: string[];
  };
  generated_questions: string[];
  session_id: string;
  processing_time: number;
}

export interface AnswerResponse {
  type: "answer";
  answer: string;
  context_info: {
    nucleus_chunks: number;
    context_length: number;
    source_collections: string[];
    source_documents: string[];
  };
  session_id: string;
  processing_time: number;
}

export type ChatResponse = ClarificationResponse | AnswerResponse;
