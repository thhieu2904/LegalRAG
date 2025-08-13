import React, { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import { chatApi } from "../services/api";
import type { Message } from "../types/chat";

interface ClarificationOption {
  id: string;
  title: string;
  description: string;
  confidence?: string;
  examples?: string[];
  action: string;
  collection?: string;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Kiểm tra kết nối backend khi component mount
    checkConnection();
  }, []);

  const checkConnection = async () => {
    try {
      await chatApi.checkHealth();
      setIsConnected(true);
    } catch (error) {
      console.error("Lỗi kết nối backend:", error);
      setIsConnected(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage({
        query: inputValue,
        max_tokens: 2048,
        temperature: 0.1,
        top_k: 5,
      });

      if (response.type === "clarification_needed") {
        // Handle clarification response - fix nested structure access
        const clarificationData =
          response.clarification?.clarification || response.clarification;
        const clarificationMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "clarification",
          content:
            clarificationData?.message || "Bạn có thể làm rõ câu hỏi không?",
          timestamp: new Date(),
          clarificationOptions: clarificationData?.options || [],
          clarificationStyle: clarificationData?.style || "default",
          session_id: response.session_id,
          processing_time: response.processing_time,
        };
        setMessages((prev) => [...prev, clarificationMessage]);
      } else if (response.type === "answer") {
        // Handle answer response
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "assistant",
          content: response.answer || "Không có câu trả lời",
          timestamp: new Date(),
          sources: response.context_info?.source_documents || [],
          source_files: response.context_info?.source_collections || [],
          processing_time: response.processing_time,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("Lỗi khi gửi tin nhắn:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content:
          "Xin lỗi, đã có lỗi xảy ra khi xử lý tin nhắn của bạn. Vui lòng thử lại sau.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClarificationSelect = async (
    option: ClarificationOption,
    sessionId?: string
  ) => {
    // Add user's selection as a message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: `Đã chọn: ${option.title}`,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send follow-up query based on selection
      let followUpQuery = "";

      if (
        option.action === "proceed_with_collection" ||
        option.action === "proceed_with_routing"
      ) {
        followUpQuery = `Tôi muốn biết về ${option.title}`;
      } else if (option.action === "explore_category") {
        followUpQuery = `Hãy giải thích về ${option.title}`;
      } else {
        followUpQuery = option.title;
      }

      const response = await chatApi.sendMessage({
        query: followUpQuery,
        session_id: sessionId,
        max_tokens: 2048,
        temperature: 0.1,
        top_k: 5,
      });

      if (response.type === "answer") {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: "assistant",
          content: response.answer || "Không có câu trả lời",
          timestamp: new Date(),
          sources: response.context_info?.source_documents || [],
          source_files: response.context_info?.source_collections || [],
          processing_time: response.processing_time,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error("Lỗi khi xử lý clarification:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Legal RAG Chat</h2>
        <div
          className={`connection-status ${
            isConnected === null
              ? "checking"
              : isConnected
              ? "connected"
              : "disconnected"
          }`}
        >
          {isConnected === null
            ? "🔍 Đang kiểm tra..."
            : isConnected
            ? "🟢 Đã kết nối"
            : "🔴 Mất kết nối"}
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Chào mừng bạn đến với Legal RAG Chat!</p>
            <p>Bạn có thể đặt câu hỏi về các tài liệu pháp luật.</p>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            onClarificationSelect={handleClarificationSelect}
          />
        ))}

        {isLoading && (
          <div className="loading-message">
            <div className="loading-dots">
              <span>Đang xử lý</span>
              <span>.</span>
              <span>.</span>
              <span>.</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Nhập câu hỏi của bạn..."
          disabled={isLoading || !isConnected}
          rows={3}
        />
        <button
          onClick={handleSendMessage}
          disabled={!inputValue.trim() || isLoading || !isConnected}
        >
          {isLoading ? "Đang gửi..." : "Gửi"}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
