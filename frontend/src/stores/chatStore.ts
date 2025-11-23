/**
 * Chat Store - Zustand State Management
 */

import { create } from 'zustand';
import type { ChatMessage, Message, ChatFilters } from '@/types';
import type { FilterOptions } from '@/types/common.types';
import { CHAT_STORAGE_KEY } from '@/constants';
import { getStorageItem, setStorageItem } from '@/utils';
import { sendChatMessage } from '@/services/query/queryService';

interface ChatState {
  // Messages
  messages: ChatMessage[];
  addMessage: (message: ChatMessage) => void;
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
    const { addMessage, setLoading, setError } = get();

    // Create and add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    addMessage(userMessage);

    // Call API
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        question,
        top_k: 5,
        threshold: 0.7,
      });

      // Create and add AI response
      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
        tokens: response.tokens_used,
      };
      addMessage(aiMessage);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Có lỗi xảy ra khi gửi tin nhắn';
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
