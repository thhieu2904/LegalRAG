/**
 * 🏗️ CLEAN ARCHITECTURE STRUCTURE FOR REACT MICROSERVICE
 *
 * Domain Layer (Innermost) - Business Logic & Entities
 * Application Layer - Use Cases & Application Services
 * Infrastructure Layer - External Services, APIs, Storage
 * Presentation Layer (Outermost) - UI Components, Pages
 */

// ========================================
// DOMAIN LAYER - Business Entities
// ========================================

export interface User {
  id: string;
  name: string;
  role: "admin" | "user";
}

export interface ChatMessage {
  id: string;
  content: string;
  type: "user" | "bot";
  timestamp: Date;
  status: "sending" | "sent" | "error";
}

export interface OCRData {
  id: string;
  imageUrl: string;
  extractedText: string;
  confidence: number;
  processedAt: Date;
}

// Domain Services (Business Rules)
export class ChatDomainService {
  static validateMessage(message: string): boolean {
    return message.trim().length > 0 && message.length <= 1000;
  }

  static formatTimestamp(date: Date): string {
    return new Intl.DateTimeFormat("vi-VN").format(date);
  }
}

// ========================================
// APPLICATION LAYER - Use Cases
// ========================================

export interface IChatRepository {
  sendMessage(message: string): Promise<string>;
  getHistory(): Promise<ChatMessage[]>;
}

export interface IOCRRepository {
  processImage(imageFile: File): Promise<OCRData>;
  getHistory(): Promise<OCRData[]>;
}

export interface INotificationService {
  showSuccess(message: string): void;
  showError(message: string): void;
}

// Use Cases
export class SendMessageUseCase {
  constructor(
    private chatRepo: IChatRepository,
    private notificationService: INotificationService
  ) {}

  async execute(message: string): Promise<ChatMessage> {
    // Domain validation
    if (!ChatDomainService.validateMessage(message)) {
      throw new Error("Invalid message");
    }

    try {
      const response = await this.chatRepo.sendMessage(message);

      const chatMessage: ChatMessage = {
        id: crypto.randomUUID(),
        content: response,
        type: "bot",
        timestamp: new Date(),
        status: "sent",
      };

      this.notificationService.showSuccess("Message sent successfully");
      return chatMessage;
    } catch (error) {
      this.notificationService.showError("Failed to send message");
      throw error;
    }
  }
}

export class ProcessImageUseCase {
  constructor(
    private ocrRepo: IOCRRepository,
    private notificationService: INotificationService
  ) {}

  async execute(imageFile: File): Promise<OCRData> {
    try {
      const result = await this.ocrRepo.processImage(imageFile);
      this.notificationService.showSuccess("Image processed successfully");
      return result;
    } catch (error) {
      this.notificationService.showError("Failed to process image");
      throw error;
    }
  }
}
