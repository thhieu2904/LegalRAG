import React, { useState, useRef, useEffect } from "react";
import "../styles/ChatPage.css";
import { apiService } from "../services/api";

// Speech Recognition interface
interface SpeechRecognitionEvent {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  length: number;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: any) => void;
  onend: () => void;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

// Enhanced ID generation system
let messageIdCounter = 0;
const generateUniqueId = (): string => {
  messageIdCounter += 1;
  return `msg_${Date.now()}_${messageIdCounter}_${Math.random()
    .toString(36)
    .substr(2, 9)}`;
};

// Professional minimal icons
const SendIcon = () => <span className="icon">→</span>;
const BotIcon = () => <span className="icon">🤖</span>;
const UserIcon = () => <span className="icon">👤</span>;
const MicIcon = () => <span className="icon">🎤</span>;
const MicOffIcon = () => <span className="icon">⏹</span>;

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

interface ContextInfo {
  nucleus_chunks: number;
  context_length: number;
  source_collections: string[];
  source_documents: string[];
}

interface ApiResponse {
  type: string;
  answer?: string;
  clarification?: ClarificationData;
  session_id: string;
  processing_time: number;
  context_info?: ContextInfo;
  error?: string;
}

interface CurrentClarification {
  clarification: ClarificationData;
  originalQuery: string;
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: generateUniqueId(),
      type: "system",
      content:
        "Xin chào! Tôi là trợ lý pháp luật AI. Tôi có thể giúp bạn tìm hiểu về các thủ tục hành chính như hộ tịch, chứng thực, và nuôi con nuôi. Bạn có câu hỏi gì không?",
      timestamp: new Date(),
    },
  ]);

  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentClarification, setCurrentClarification] =
    useState<CurrentClarification | null>(null);

  // Voice recognition state
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(
    null
  );

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  // Initialize speech recognition
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      (window.SpeechRecognition || window.webkitSpeechRecognition)
    ) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();

      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = "vi-VN"; // Vietnamese language

      recognitionInstance.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsListening(false);
      };

      recognitionInstance.onerror = () => {
        setIsListening(false);
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }
  }, []);

  const startListening = () => {
    if (recognition && !isListening) {
      setIsListening(true);
      recognition.start();
    }
  };

  const stopListening = () => {
    if (recognition && isListening) {
      setIsListening(false);
      recognition.stop();
    }
  };

  const sendQuery = async (userQuery: string) => {
    if (userQuery.trim() === "" || isLoading) return;

    // Add user message with unique ID
    const userMessage: Message = {
      id: generateUniqueId(),
      type: "user",
      content: userQuery,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setCurrentClarification(null);

    try {
      const result = await apiService.sendQuery(userQuery, sessionId);
      setSessionId(result.session_id);
      handleApiResponse(result, userQuery);
    } catch (error) {
      console.error("Error sending query:", error);
      addAssistantMessage("Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApiResponse = (result: ApiResponse, userQuery: string) => {
    if (result.type === "answer" && result.answer) {
      addAssistantMessage(
        result.answer,
        false,
        result.processing_time,
        result.context_info?.source_documents
      );
      setCurrentClarification(null);
    } else if (result.type === "clarification_needed" && result.clarification) {
      setCurrentClarification({
        clarification: result.clarification,
        originalQuery: result.clarification.original_query || userQuery,
      });

      const clarificationMessage =
        result.clarification.message || "Vui lòng chọn một tùy chọn:";

      addAssistantMessage(
        clarificationMessage,
        false,
        result.processing_time,
        result.context_info?.source_documents,
        result.clarification
      );
    } else if (result.type === "no_results") {
      addAssistantMessage(
        "Xin lỗi, tôi không tìm thấy thông tin phù hợp với câu hỏi của bạn. Bạn có thể thử hỏi cách khác không?",
        false,
        result.processing_time,
        result.context_info?.source_documents
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
      id: generateUniqueId(),
      type: isError ? "system" : "assistant",
      content: content,
      timestamp: new Date(),
      clarification: clarification,
      processingTime: processingTime,
      sourceDocuments: sourceDocuments,
    };

    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleCollectionSelection = async (
    selectedOption: ClarificationOption,
    originalQuery: string
  ) => {
    if (!sessionId) return;

    setIsLoading(true);

    try {
      const result = await apiService.sendClarificationResponse(
        sessionId,
        originalQuery,
        selectedOption
      );
      handleApiResponse(result, `Đã chọn: ${selectedOption.title}`);
    } catch (error) {
      console.error("Collection selection error:", error);
      addAssistantMessage("Có lỗi xảy ra khi xử lý lựa chọn của bạn.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionSelection = async (
    selectedOption: ClarificationOption,
    originalQuery: string
  ) => {
    if (!sessionId) return;

    setIsLoading(true);

    try {
      const result = await apiService.sendClarificationResponse(
        sessionId,
        originalQuery,
        selectedOption
      );
      handleApiResponse(result, `Đã chọn: ${selectedOption.title}`);
    } catch (error) {
      console.error("Question selection error:", error);
      addAssistantMessage("Có lỗi xảy ra khi xử lý câu hỏi của bạn.", true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuery(inputValue);
  };

  const handleOptionClick = (option: ClarificationOption) => {
    if (!currentClarification) return;

    const { originalQuery } = currentClarification;

    // Add user selection message with unique ID
    const userMessage: Message = {
      id: generateUniqueId(),
      type: "user",
      content: `Đã chọn: ${option.title}`,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    if (option.action === "proceed_with_collection") {
      handleCollectionSelection(option, originalQuery);
    } else if (option.action === "proceed_with_question") {
      handleQuestionSelection(option, originalQuery);
    } else if (option.action === "manual_input") {
      setCurrentClarification(null);
      addAssistantMessage("Vui lòng nhập câu hỏi cụ thể của bạn:");
    }
  };

  const renderClarificationOptions = (clarification: ClarificationData) => {
    if (!clarification?.options || clarification.options.length === 0) {
      return null;
    }

    return (
      <div className="clarification-options">
        {clarification.options.map((option) => (
          <div
            key={option.id}
            className={`option-card ${
              option.action === "proceed_with_collection"
                ? "collection-option"
                : "question-option"
            }`}
            onClick={() => handleOptionClick(option)}
          >
            <div className="option-header">
              <h4>{option.title}</h4>
              {option.confidence && (
                <span className="confidence-badge">{option.confidence}</span>
              )}
            </div>
            {option.description && (
              <p className="option-description">{option.description}</p>
            )}
            {option.examples && option.examples.length > 0 && (
              <div className="option-examples">
                Ví dụ: {option.examples.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  const formatFileName = (filePath: string): string => {
    const fileName =
      filePath.split("\\").pop()?.replace(".json", "") || filePath;
    return fileName;
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
            <span className="system-icon">i</span>
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
                📄 Nguồn tài liệu tham khảo:
              </div>
              <div className="source-documents-list">
                {message.sourceDocuments.map((doc, index) => (
                  <div key={index} className="source-document">
                    {formatFileName(doc)}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="message-meta">
            <span className="message-time">
              {message.timestamp.toLocaleTimeString("vi-VN", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </span>
            {message.processingTime && message.processingTime > 0 && (
              <span className="processing-time">
                {message.processingTime.toFixed(2)}s
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="chat-page">
      {/* Main Card Container wrapping everything */}
      <div className="main-card">
        <div className="chat-header">
          <div className="header-content">
            <div className="header-title">
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
                placeholder="Nhập câu hỏi của bạn hoặc nhấn mic để nói..."
                disabled={isLoading || isListening}
                className="message-input"
              />

              {/* Voice Input Button */}
              {recognition && (
                <button
                  type="button"
                  onClick={isListening ? stopListening : startListening}
                  disabled={isLoading}
                  className={`voice-button ${isListening ? "listening" : ""}`}
                  title={isListening ? "Nhấn để dừng ghi âm" : "Nhấn để nói"}
                >
                  {isListening ? <MicOffIcon /> : <MicIcon />}
                </button>
              )}

              <button
                type="submit"
                disabled={isLoading || inputValue.trim() === "" || isListening}
                className="send-button"
              >
                <SendIcon />
              </button>
            </div>

            <div className="input-help">
              💡{" "}
              <span>
                Ví dụ: "thủ tục khai sinh cần gì", "làm chứng thực bản sao"
                {recognition && " | Nhấn mic để nhập bằng giọng nói"}
              </span>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
