/**
 * Chat Store - Zustand State Management
 */

import { create } from 'zustand';
import type { ChatMessage, Message, ChatFilters, HistoryMessage } from '@/types';
import type { FilterOptions } from '@/types/common.types';
import { CHAT_STORAGE_KEY } from '@/constants';
import { getStorageItem, setStorageItem } from '@/utils';
import { sendChatMessage, confirmDocument } from '@/services/query/queryService';

/**
 * Build history for API from messages (last 3 Q&A turns, truncated)
 * Truncates assistant answers to 300 chars to save tokens
 */
const buildHistoryForAPI = (messages: ChatMessage[]): HistoryMessage[] => {
  // Filter to only user and assistant messages (exclude clarification)
  const validMessages = messages.filter(
    (m) => (m.role === 'user' || m.role === 'assistant') && !m.needs_clarification
  );

  // Take last 6 messages (3 turns: user + assistant)
  const recentMessages = validMessages.slice(-6);

  // Map to API format with truncation for assistant messages
  return recentMessages.map((m) => ({
    role: m.role as 'user' | 'assistant',
    content:
      m.role === 'assistant' && m.content.length > 300
        ? m.content.slice(0, 300) + '...'
        : m.content,
  }));
};

interface ChatState {
  // Messages
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;

  // Conversation history (for API)
  conversationHistory: Message[];
  addToHistory: (message: Message) => void;
  clearHistory: () => void;

  // Filters
  filters: ChatFilters;
  setFilters: (filters: ChatFilters) => void;
  clearFilters: () => void;

  // UI State
  loading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;

  // Actions
  sendMessage: (message: string, filters: FilterOptions) => Promise<void>;
  selectDocument: (
    originalQuestion: string,
    documentId: string,
    documentTitle: string
  ) => Promise<void>;

  // Persistence
  loadFromStorage: () => void;
  saveToStorage: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  conversationHistory: [],
  filters: {},
  loading: false,
  error: null,

  // Add message to UI
  addMessage: (message) =>
    set((state) => {
      const newMessages = [...state.messages, message];
      // Auto-save to storage
      setStorageItem(CHAT_STORAGE_KEY, newMessages);
      return { messages: newMessages };
    }),

  // Update existing message (for replacing clarification with answer)
  updateMessage: (id, updates) =>
    set((state) => {
      const newMessages = state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      );
      setStorageItem(CHAT_STORAGE_KEY, newMessages);
      return { messages: newMessages };
    }),

  // Clear all messages
  clearMessages: () =>
    set(() => {
      setStorageItem(CHAT_STORAGE_KEY, []);
      return { messages: [], conversationHistory: [] };
    }),

  // Add to conversation history (for API context)
  addToHistory: (message) =>
    set((state) => ({
      conversationHistory: [...state.conversationHistory, message],
    })),

  // Clear conversation history
  clearHistory: () =>
    set(() => ({
      conversationHistory: [],
    })),

  // Set filters
  setFilters: (filters) =>
    set(() => ({
      filters,
    })),

  // Clear filters
  clearFilters: () =>
    set(() => ({
      filters: {},
    })),

  // Set loading state
  setLoading: (loading) =>
    set(() => ({
      loading,
    })),

  // Set error
  setError: (error) =>
    set(() => ({
      error,
    })),

  // Send message (call API and update state)
  sendMessage: async (question: string, filters: FilterOptions) => {
    const { messages, addMessage, setLoading, setError } = get();

    // Create and add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // Build history from previous messages (before adding current question)
    const history = buildHistoryForAPI(messages);

    // Call API
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        question,
        top_k: 5,
        threshold: 0.7,
        history: history.length > 0 ? history : undefined,
      });

      // Check if clarification needed
      if (response.needs_clarification && response.document_options) {
        // Create clarification message with options
        const clarificationMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content:
            response.clarification_message ||
            'Tôi tìm thấy nhiều văn bản liên quan. Bạn muốn xem văn bản nào?',
          timestamp: new Date(),
          needs_clarification: true,
          document_options: response.document_options,
          originalQuestion: question, // Store for confirm request
        };
        addMessage(clarificationMessage);
      } else {
        // Direct answer
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.answer || 'Không có câu trả lời.',
          sources: response.sources,
          timestamp: new Date(),
          tokens: response.tokens_used,
        };
        addMessage(aiMessage);
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Có lỗi xảy ra khi gửi tin nhắn';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  },

  // Handle document selection (after clarification)
  selectDocument: async (originalQuestion: string, documentId: string, documentTitle: string) => {
    const { messages, addMessage, setLoading, setError } = get();

    // Add user selection as a message
    const selectionMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: `📄 Chọn: ${documentTitle}`,
      timestamp: new Date(),
    };
    addMessage(selectionMessage);

    // Build history from previous messages
    const history = buildHistoryForAPI(messages);

    // Call confirm API
    setLoading(true);
    setError(null);

    try {
      const response = await confirmDocument({
        question: originalQuestion,
        document_id: documentId,
        history: history.length > 0 ? history : undefined,
      });

      // Add answer
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer || 'Không tìm thấy thông tin trong văn bản đã chọn.',
        sources: response.sources,
        timestamp: new Date(),
        tokens: response.tokens_used,
      };
      addMessage(aiMessage);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Có lỗi xảy ra khi xử lý yêu cầu';
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  },

  // Load messages from localStorage
  loadFromStorage: () => {
    const storedMessages = getStorageItem<ChatMessage[]>(CHAT_STORAGE_KEY, []);
    set({ messages: storedMessages });
  },

  // Save messages to localStorage
  saveToStorage: () => {
    const { messages } = get();
    setStorageItem(CHAT_STORAGE_KEY, messages);
  },
}));
