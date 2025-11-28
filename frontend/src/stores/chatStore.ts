/**
 * Chat Store - Zustand State Management
 *
 * Session Management:
 * - Session is now managed by BACKEND (query-service)
 * - Frontend sends session_id=null on first request (F5/new tab)
 * - Backend generates session_id in format YYYYMMDD_NNNN
 * - Frontend stores and reuses session_id for subsequent requests
 * - Explicit "clear session" button calls /session/clear endpoint
 */

import { create } from 'zustand';
import type { ChatMessage, Message, ChatFilters, HistoryMessage } from '@/types';
import type { FilterOptions } from '@/types/common.types';
import { CHAT_STORAGE_KEY } from '@/constants';
import { getStorageItem, setStorageItem } from '@/utils';
import { sendChatMessage, confirmDocument, clearSession } from '@/services/query/queryService';

// Storage keys for session
const SESSION_ID_KEY = 'legalrag_session_id';
const SESSION_INIT_KEY = 'legalrag_session_initialized';

/**
 * Get current session ID from sessionStorage (if any).
 * Returns null if no session exists (will trigger backend to create one).
 */
const getCurrentSessionId = (): string | null => {
  // Check if this is a fresh page load (F5/refresh or new tab)
  const isInitialized = sessionStorage.getItem(SESSION_INIT_KEY);

  if (!isInitialized) {
    // Fresh page load - clear old session to trigger new session from backend
    sessionStorage.removeItem(SESSION_ID_KEY);
    sessionStorage.setItem(SESSION_INIT_KEY, 'true');
    console.log('🔄 New page load - will request new session from backend');
    return null;
  }

  // Return existing session ID (or null if not set)
  return sessionStorage.getItem(SESSION_ID_KEY);
};

/**
 * Save session ID received from backend
 */
const saveSessionId = (sessionId: string): void => {
  sessionStorage.setItem(SESSION_ID_KEY, sessionId);
  console.log(`📌 Session saved: ${sessionId}`);
};

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
  clearCurrentSession: () => Promise<void>; // Clear pinned document

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

  // Clear all messages and reset session
  clearMessages: () =>
    set(() => {
      setStorageItem(CHAT_STORAGE_KEY, []);
      // Also reset session ID to clear pinned document state
      sessionStorage.removeItem('legalrag_session_id');
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
  sendMessage: async (question: string, _filters: FilterOptions) => {
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

    // Call API with session_id (null = request new session from backend)
    setLoading(true);
    setError(null);

    try {
      const sessionId = getCurrentSessionId(); // null on first request (F5/new tab)

      const response = await sendChatMessage({
        question,
        session_id: sessionId, // Backend will create new session if null
        top_k: 5,
        threshold: 0.7,
        history: history.length > 0 ? history : undefined,
      });

      // Save session_id from response for subsequent requests
      if (response.session_id) {
        saveSessionId(response.session_id);
      }

      // Log session info (for debugging)
      if (response.session_info) {
        console.log(
          `📌 Session: ${response.session_id}, New: ${response.session_info.is_new_session}, Pinned: ${response.session_info.pinned_document_title || 'none'}`
        );
      }

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

    // Call confirm API with existing session
    setLoading(true);
    setError(null);

    try {
      const sessionId = getCurrentSessionId(); // Should have session from previous request

      const response = await confirmDocument({
        question: originalQuestion,
        document_id: documentId,
        session_id: sessionId, // Use existing session
        history: history.length > 0 ? history : undefined,
      });

      // Save session_id from response (in case it was created)
      if (response.session_id) {
        saveSessionId(response.session_id);
      }

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

  // Clear session (unpin document)
  clearCurrentSession: async () => {
    const { setLoading, setError } = get();
    const sessionId = getCurrentSessionId();

    if (!sessionId) {
      console.log('📌 No session to clear');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await clearSession({ session_id: sessionId });
      console.log(`📌 Session cleared: ${sessionId}`);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Lỗi khi xóa session';
      setError(errorMessage);
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
