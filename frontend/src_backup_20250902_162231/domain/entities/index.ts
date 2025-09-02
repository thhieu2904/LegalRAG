/**
 * 🏢 DOMAIN ENTITIES
 * Core business objects - không phụ thuộc vào bất kỳ layer nào khác
 */

export interface User {
  id: string;
  name: string;
  email: string;
  role: "admin" | "user";
  createdAt: Date;
}

export interface ChatMessage {
  id: string;
  content: string;
  type: "user" | "bot";
  timestamp: Date;
  status: "sending" | "sent" | "error";
  metadata?: {
    sources?: string[];
    confidence?: number;
  };
}

export interface ChatSession {
  id: string;
  userId: string;
  messages: ChatMessage[];
  startedAt: Date;
  endedAt?: Date;
}

export interface OCRResult {
  id: string;
  imageUrl: string;
  extractedData: {
    idNumber: string;
    fullName: string;
    dateOfBirth: string;
    placeOfBirth: string;
    address: string;
    issueDate: string;
    expiryDate?: string;
  };
  confidence: number;
  processedAt: Date;
  status: "processing" | "completed" | "failed";
}

export interface AdminStats {
  totalUsers: number;
  totalChats: number;
  totalOCRProcessed: number;
  systemStatus: "healthy" | "warning" | "error";
  lastUpdated: Date;
}

// Value Objects (immutable objects that represent a descriptive aspect)
export class MessageContent {
  constructor(private readonly value: string) {
    if (!value || value.trim().length === 0) {
      throw new Error("Message content cannot be empty");
    }
    if (value.length > 1000) {
      throw new Error("Message content too long");
    }
  }

  getValue(): string {
    return this.value;
  }

  toString(): string {
    return this.value;
  }
}
