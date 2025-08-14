export interface Message {
  id: string;
  type: "user" | "assistant" | "clarification";
  content: string;
  timestamp: Date;
  sources?: string[];
  source_files?: string[];
  processing_time?: number;
  clarificationOptions?: Array<{
    id: string;
    title: string;
    description: string;
    confidence?: string;
    examples?: string[];
    action: string;
    collection?: string;
  }>;
  clarificationStyle?: string;
  session_id?: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string | null;
  max_context_length?: number;
  use_ambiguous_detection?: boolean;
  use_full_document_expansion?: boolean;
  forced_collection?: string | null;
}

export interface ClarificationResponse {
  type: "clarification_needed";
  confidence_level?: string;
  confidence: number;
  clarification: {
    message?: string;
    options?: Array<{
      id: string;
      title: string;
      description: string;
      confidence?: string;
      examples?: string[];
      action: string;
      collection?: string;
    }>;
    style?: string;
    additional_help?: string;
    // Support nested structure from backend
    clarification?: {
      message: string;
      options: Array<{
        id: string;
        title: string;
        description: string;
        confidence?: string;
        examples?: string[];
        action: string;
        collection?: string;
      }>;
      style: string;
      additional_help?: string;
    };
  };
  routing_context: Record<string, unknown>;
  strategy: string;
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
