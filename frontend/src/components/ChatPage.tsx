import React, { useState, useRef, useEffect } from "react";
import "../styles/ChatPage.css";

// Simple icon components to replace lucide-react
const SendIcon = () => <span className="icon">➤</span>;
const BotIcon = () => <span className="icon">🤖</span>;
const UserIcon = () => <span className="icon">👤</span>;
const ClockIcon = () => <span className="icon">⏰</span>;
const AlertIcon = () => <span className="icon">⚠️</span>;
const HelpIcon = () => <span className="icon">💡</span>;

interface Message {
  id: string;
  type: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  clarification?: ClarificationData;
  processing?: boolean;
  processingTime?: number;
  sourceDocuments?: string[];
}

interface ClarificationOption {
  id: string;
  title: string;
  description: string;
  confidence?: string;
  examples?: string[];
  action: string;
  collection?: string;
  question_text?: string;
  category?: string;
}

interface ClarificationData {
  message: string;
  options: ClarificationOption[];
  style: string;
  stage?: number;
  collection?: string;
  original_query?: string;
}

interface ApiResponse {
  type: string;
  answer?: string;
  clarification?: ClarificationData;
  session_id: string;
  processing_time: number;
  source_documents?: string[];
  error?: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "system",
      content:
        "Xin chào! Tôi là trợ lý pháp luật AI. Tôi có thể giúp bạn tìm hiểu về các thủ tục hành chính như hộ tịch, chứng thực, và nuôi con nuôi. Bạn có câu hỏi gì không?",
      timestamp: new Date(),
    },
  ]);

  const [inputValue, setInputValue] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentClarification, setCurrentClarification] = useState<{
    clarification: ClarificationData;
    originalQuery: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 🔧 CORE FIX: Proper API integration with multi-turn clarification
  const sendQuery = async (query: string, isInitial: boolean = true) => {
    if (query.trim() === "" && isInitial) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: query,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const payload = {
        query: query.trim(),
        session_id: sessionId,
      };

      const response = await fetch("/api/v2/optimized-query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result: ApiResponse = await response.json();

      if (!sessionId && result.session_id) {
        setSessionId(result.session_id);
      }

      handleApiResponse(result, query);
    } catch (error) {
      console.error("Error:", error);
      addAssistantMessage(
        "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.",
        true
      );
    } finally {
      setIsLoading(false);
      if (isInitial) {
        setInputValue("");
      }
    }
  };

  // 🎯 GIAI ĐOẠN 2→3: Handle collection selection → Get question suggestions
  const handleCollectionSelection = async (
    selectedOption: ClarificationOption,
    originalQuery: string
  ) => {
    if (!sessionId || !currentClarification) return;

    setIsLoading(true);

    try {
      // ✅ CORRECT FORMAT: Send to clarification endpoint
      const payload = {
        session_id: sessionId,
        original_query: originalQuery,
        selected_option: selectedOption,
      };

      const response = await fetch("/api/v2/clarify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result: ApiResponse = await response.json();
      handleApiResponse(result, `Đã chọn: ${selectedOption.title}`);
    } catch (error) {
      console.error("Collection selection error:", error);
      addAssistantMessage("Có lỗi xảy ra khi xử lý lựa chọn của bạn.", true);
    } finally {
      setIsLoading(false);
    }
  };

  // 🎯 GIAI ĐOẠN 3→4: Handle question selection → Get final answer
  const handleQuestionSelection = async (
    selectedOption: ClarificationOption,
    originalQuery: string
  ) => {
    if (!sessionId) return;

    setIsLoading(true);

    try {
      // ✅ CORRECT FORMAT: Send to clarification endpoint with question_text
      const payload = {
        session_id: sessionId,
        original_query: originalQuery,
        selected_option: selectedOption,
      };

      const response = await fetch("/api/v2/clarify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result: ApiResponse = await response.json();
      handleApiResponse(result, `Đã chọn: ${selectedOption.title}`);
    } catch (error) {
      console.error("Question selection error:", error);
      addAssistantMessage("Có lỗi xảy ra khi xử lý câu hỏi của bạn.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiResponse = (result: ApiResponse, userQuery: string) => {
    if (result.type === "answer") {
      // Final answer received
      addAssistantMessage(
        result.answer || "",
        false,
        result.processing_time,
        result.source_documents
      );
      setCurrentClarification(null);
    } else if (result.type === "clarification_needed" && result.clarification) {
      // Clarification needed - could be collection selection or question suggestions
      setCurrentClarification({
        clarification: result.clarification,
        originalQuery: result.clarification.original_query || userQuery,
      });

      let clarificationMessage = result.clarification.message;
      if (result.clarification.style === "question_suggestion") {
        clarificationMessage +=
          "\n\n💡 Chọn một câu hỏi cụ thể để tôi có thể trả lời chính xác nhất:";
      }

      addAssistantMessage(
        clarificationMessage,
        false,
        result.processing_time,
        result.source_documents,
        result.clarification
      );
    } else if (result.type === "no_results") {
      addAssistantMessage(
        "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn. Bạn có thể thử hỏi cách khác không?",
        false,
        result.processing_time,
        result.source_documents
      );
      setCurrentClarification(null);
    } else if (result.type === "error") {
      addAssistantMessage(`Có lỗi xảy ra: ${result.error}`, true);
      setCurrentClarification(null);
    }
  };

  const addAssistantMessage = (
    content: string,
    isError: boolean = false,
    processingTime?: number,
    sourceDocuments?: string[],
    clarification?: ClarificationData
  ) => {
    const assistantMessage: Message = {
      id: Date.now().toString(),
      type: isError ? "system" : "assistant",
      content: content,
      timestamp: new Date(),
      clarification: clarification,
      processingTime: processingTime,
      sourceDocuments: sourceDocuments,
    };

    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(inputValue);
  };

  const handleOptionClick = (option: ClarificationOption) => {
    if (!currentClarification) return;

    const { originalQuery } = currentClarification;

    // Add user selection message
    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: `Đã chọn: ${option.title}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    if (option.action === "proceed_with_collection") {
      // GIAI ĐOẠN 2→3: Collection selected, get question suggestions
      handleCollectionSelection(option, originalQuery);
    } else if (option.action === "proceed_with_question") {
      // GIAI ĐOẠN 3→4: Question selected, get final answer
      handleQuestionSelection(option, originalQuery);
    } else if (option.action === "manual_input") {
      // Manual input requested
      setCurrentClarification(null);
      addAssistantMessage("Vui lòng nhập câu hỏi cụ thể của bạn:");
    }
  };

  const renderClarificationOptions = (clarification: ClarificationData) => {
    return (
      <div className="clarification-options">
        {clarification.options.map((option) => (
          <div
            key={option.id}
            className={`option-card ${
              clarification.style === "question_suggestion"
                ? "question-option"
                : "collection-option"
            }`}
            onClick={() => handleOptionClick(option)}
          >
            <div className="option-header">
              <h4>{option.title}</h4>
              {option.confidence && (
                <span className="confidence-badge">
                  Độ tin cậy: {option.confidence}
                </span>
              )}
            </div>

            <p className="option-description">{option.description}</p>

            {option.examples && option.examples.length > 0 && (
              <div className="option-examples">
                <small>Ví dụ: {option.examples.join(", ")}</small>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderMessage = (message: Message) => {
    return (
      <div key={message.id} className={`message ${message.type}`}>
        <div className="message-avatar">
          {message.type === "user" ? (
            <UserIcon />
          ) : message.type === "assistant" ? (
            <BotIcon />
          ) : (
            <AlertIcon />
          )}
        </div>

        <div className="message-content">
          <div className="message-text">{message.content}</div>

          {message.clarification && (
            <div className="clarification-container">
              {renderClarificationOptions(message.clarification)}
            </div>
          )}

          {/* Source Documents */}
          {message.sourceDocuments && message.sourceDocuments.length > 0 && (
            <div className="source-documents">
              <div className="source-documents-header">
                📁 Nguồn tài liệu tham khảo:
              </div>
              <div className="source-documents-list">
                {message.sourceDocuments.map((doc, index) => (
                  <div key={index} className="source-document">
                    {doc.split("\\").pop()?.replace(".json", "") || doc}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="message-meta">
            <span className="message-time">
              <ClockIcon />
              {message.timestamp.toLocaleTimeString()}
            </span>
            {message.processingTime && message.processingTime > 0 && (
              <span className="processing-time">
                ⚡ {message.processingTime.toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div className="header-content">
          <div className="header-title">
            <BotIcon />
            <h1>Trợ lý Pháp luật AI</h1>
          </div>
          <div className="header-subtitle">
            Hệ thống hỗ trợ thông tin thủ tục hành chính
          </div>
        </div>
      </div>

      <div className="chat-container">
        <div className="messages-container">
          {messages.map(renderMessage)}

          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">
                <BotIcon />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="input-container">
          <div className="input-wrapper">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Nhập câu hỏi của bạn..."
              disabled={isLoading}
              className="message-input"
            />
            <button
              type="submit"
              disabled={isLoading || inputValue.trim() === ""}
              className="send-button"
            >
              <SendIcon />
            </button>
          </div>

          <div className="input-help">
            <HelpIcon />
            <span>
              Ví dụ: "thủ tục khai sinh cần gì", "làm chứng thực bản sao"
            </span>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatPage;
