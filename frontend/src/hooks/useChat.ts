import { useState, useCallback, useEffect } from "react";
import {
  ChatService,
  type ClarificationData,
  type ClarificationOption,
  type ApiResponse,
  type ContextSummary,
} from "../services/chatService";

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: string;
  clarification?: ClarificationData;
  processingTime?: number;
  sourceDocuments?: string[];
  apiResponse?: ApiResponse; // Store full API response for advanced handling
}

interface UseChatOptions {
  initialMessage?: string;
  onError?: (error: Error) => void;
}

let messageIdCounter = 0;
const generateUniqueId = (): string => {
  messageIdCounter += 1;
  return `msg_${Date.now()}_${messageIdCounter}_${Math.random()
    .toString(36)
    .substr(2, 9)}`;
};

export function useChat(options: UseChatOptions = {}) {
  const [messages, setMessages] = useState<Message[]>(() => {
    const initialMessages: Message[] = [];

    if (options.initialMessage) {
      initialMessages.push({
        id: generateUniqueId(),
        content: options.initialMessage,
        isBot: true,
        timestamp: new Date().toLocaleTimeString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      });
    }

    return initialMessages;
  });

  const [isLoading, setIsLoading] = useState(false);
  const [currentClarification, setCurrentClarification] = useState<{
    clarification: ClarificationData;
    originalQuery: string;
  } | null>(null);

  // 🔥 NEW: Context management state
  const [contextSummary, setContextSummary] = useState<ContextSummary | null>(
    null
  );
  const [isContextLoading, setIsContextLoading] = useState(false);

  const addMessage = useCallback(
    (
      content: string,
      isBot: boolean,
      clarification?: ClarificationData,
      processingTime?: number,
      sourceDocuments?: string[],
      apiResponse?: ApiResponse
    ) => {
      const message: Message = {
        id: generateUniqueId(),
        content,
        isBot,
        timestamp: new Date().toLocaleTimeString("vi-VN", {
          hour: "2-digit",
          minute: "2-digit",
        }),
        clarification,
        processingTime,
        sourceDocuments,
        apiResponse,
      };

      setMessages((prev) => [...prev, message]);
      return message;
    },
    []
  );

  // 🔥 NEW: Function to update context summary
  const updateContextSummary = useCallback(async () => {
    const sessionId = ChatService.getCurrentSessionId();
    if (!sessionId) return;

    setIsContextLoading(true);
    try {
      const context = await ChatService.getSessionContext(sessionId);
      setContextSummary(context);
    } catch (error) {
      console.error("Error updating context summary:", error);
    } finally {
      setIsContextLoading(false);
    }
  }, []);

  // 🔥 NEW: Function to reset context
  const resetContext = useCallback(async () => {
    const sessionId = ChatService.getCurrentSessionId();
    if (!sessionId) return;

    setIsContextLoading(true);
    try {
      const success = await ChatService.resetSessionContext(sessionId);
      if (success) {
        // Clear messages on frontend as well
        setMessages([]);
        setCurrentClarification(null);
        setContextSummary(null);

        // Optionally add a system message
        addMessage(
          "Đã xóa ngữ cảnh cuộc trò chuyện. Bạn có thể bắt đầu một chủ đề mới.",
          true
        );
      }
    } catch (error) {
      console.error("Error resetting context:", error);
      addMessage("Có lỗi khi xóa ngữ cảnh. Vui lòng thử lại.", true);
    } finally {
      setIsContextLoading(false);
    }
  }, [addMessage]);

  // 🔥 NEW: Auto update context summary when session exists
  useEffect(() => {
    const sessionId = ChatService.getCurrentSessionId();
    if (sessionId) {
      updateContextSummary();
    }
  }, [updateContextSummary]);

  const sendMessage = useCallback(
    async (content: string) => {
      // Add user message
      addMessage(content, false);
      setIsLoading(true);
      setCurrentClarification(null);

      try {
        const response = await ChatService.sendMessage(content);

        if (response.apiResponse) {
          const apiResponse = response.apiResponse;

          if (apiResponse.type === "answer" && apiResponse.answer) {
            addMessage(
              apiResponse.answer,
              true,
              undefined,
              apiResponse.processing_time,
              apiResponse.context_info?.source_documents,
              apiResponse
            );
            setCurrentClarification(null);
          } else if (
            apiResponse.type === "clarification_needed" &&
            apiResponse.clarification
          ) {
            setCurrentClarification({
              clarification: apiResponse.clarification,
              originalQuery:
                apiResponse.clarification.original_query || content,
            });

            const clarificationMessage =
              apiResponse.clarification.message ||
              "Vui lòng chọn một tùy chọn:";
            addMessage(
              clarificationMessage,
              true,
              apiResponse.clarification,
              apiResponse.processing_time,
              apiResponse.context_info?.source_documents,
              apiResponse
            );
          } else if (apiResponse.type === "no_results") {
            addMessage(
              "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn. Bạn có thể thử hỏi cách khác không?",
              true,
              undefined,
              apiResponse.processing_time,
              apiResponse.context_info?.source_documents,
              apiResponse
            );
            setCurrentClarification(null);
          } else if (apiResponse.type === "error") {
            addMessage(`Có lỗi xảy ra: ${apiResponse.error}`, true);
            setCurrentClarification(null);
          }
        } else {
          // Fallback to simple response
          addMessage(
            response.response,
            true,
            undefined,
            response.processing_time,
            response.sources
          );
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Đã có lỗi xảy ra";
        addMessage(`Xin lỗi, ${errorMessage}. Vui lòng thử lại.`, true);

        if (options.onError) {
          options.onError(
            error instanceof Error ? error : new Error(errorMessage)
          );
        }
      } finally {
        setIsLoading(false);
        // 🔥 NEW: Update context summary after each interaction
        updateContextSummary();
      }
    },
    [addMessage, options, updateContextSummary]
  );

  const handleClarificationOption = useCallback(
    async (option: ClarificationOption) => {
      console.log("🔍 DEBUG: handleClarificationOption called", {
        optionId: option.id,
        optionTitle: option.title,
        currentClarificationExists: !!currentClarification,
        currentClarificationDetails: currentClarification
          ? {
              originalQuery: currentClarification.originalQuery,
              optionsCount: currentClarification.clarification.options.length,
            }
          : null,
      });

      if (!currentClarification) {
        console.warn(
          "No currentClarification found when handling option:",
          option
        );
        // 🔧 FIX: Show user-friendly message instead of silent fail
        addMessage(
          "Xin lỗi, có lỗi khi xử lý lựa chọn của bạn. Vui lòng thử lại.",
          true
        );
        return;
      }

      const { originalQuery } = currentClarification;
      console.log("Handling clarification option:", {
        option,
        originalQuery,
        sessionId: ChatService.getSessionId(),
      });

      // Add user selection message
      addMessage(`Đã chọn: ${option.title}`, false);
      setIsLoading(true);

      try {
        const sessionId = ChatService.getSessionId();
        if (!sessionId) {
          console.error("No sessionId available for clarification");
          addMessage("Không thể xử lý lựa chọn: thiếu session ID", true);
          return;
        }

        const response = await ChatService.sendClarificationResponse(
          sessionId,
          originalQuery,
          option
        );

        console.log("Clarification response:", response);

        if (response.apiResponse) {
          const apiResponse = response.apiResponse;

          if (apiResponse.type === "answer" && apiResponse.answer) {
            addMessage(
              apiResponse.answer,
              true,
              undefined,
              apiResponse.processing_time,
              apiResponse.context_info?.source_documents,
              apiResponse
            );
            // 🔧 Clear currentClarification only when we have a final answer
            console.log(
              "✅ Final answer received, clearing currentClarification"
            );
            setCurrentClarification(null);
          } else if (
            apiResponse.type === "clarification_needed" &&
            apiResponse.clarification
          ) {
            // 🔧 CRITICAL FIX: Update currentClarification state for next step
            console.log(
              "🔄 Setting new currentClarification for next step:",
              apiResponse.clarification
            );
            setCurrentClarification({
              clarification: apiResponse.clarification,
              originalQuery:
                apiResponse.clarification.original_query || originalQuery,
            });

            addMessage(
              apiResponse.clarification.message,
              true,
              apiResponse.clarification,
              apiResponse.processing_time,
              apiResponse.context_info?.source_documents,
              apiResponse
            );
          }
        } else {
          addMessage(
            response.response,
            true,
            undefined,
            response.processing_time,
            response.sources
          );
          // 🔧 Clear currentClarification for non-API responses
          console.log("✅ Non-API response, clearing currentClarification");
          setCurrentClarification(null);
        }
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Đã có lỗi xảy ra";
        addMessage(
          `Có lỗi xảy ra khi xử lý lựa chọn của bạn: ${errorMessage}`,
          true
        );
        console.error("Clarification error:", error);
      } finally {
        setIsLoading(false);
        // 🔥 NEW: Update context summary after clarification
        updateContextSummary();
      }
    },
    [currentClarification, addMessage, updateContextSummary]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentClarification(null);
    ChatService.resetSession();
  }, []);

  return {
    messages,
    isLoading,
    sendMessage,
    clearMessages,
    currentClarification,
    handleClarificationOption,
    // 🔥 NEW: Context management exports
    contextSummary,
    isContextLoading,
    resetContext,
    updateContextSummary,
  };
}
