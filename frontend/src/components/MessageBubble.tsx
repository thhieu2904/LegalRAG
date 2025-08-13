import React from "react";
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

interface MessageBubbleProps {
  message: Message;
  onClarificationSelect?: (
    option: ClarificationOption,
    sessionId?: string
  ) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onClarificationSelect,
}) => {
  const isUser = message.type === "user";
  const isClarification = message.type === "clarification";

  const handleOptionClick = (option: ClarificationOption) => {
    if (onClarificationSelect && message.session_id) {
      onClarificationSelect(option, message.session_id);
    }
  };

  return (
    <div
      className={`message-bubble ${isUser ? "user" : "assistant"} ${
        isClarification ? "clarification" : ""
      }`}
    >
      <div className="message-header">
        <span className="message-type">{isUser ? "Bạn" : "Trợ lý"}</span>
        <span className="message-time">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>

      <div className="message-content">{message.content}</div>

      {/* Render clarification options */}
      {isClarification &&
        message.clarificationOptions &&
        message.clarificationOptions.length > 0 && (
          <div className="clarification-options">
            <div className="options-container">
              {message.clarificationOptions.map((option, index) => (
                <div
                  key={option.id || index}
                  className="clarification-option"
                  onClick={() => handleOptionClick(option)}
                >
                  <div className="option-title">{option.title}</div>
                  <div className="option-description">{option.description}</div>
                  {option.confidence && (
                    <div className="option-confidence">
                      Độ tin cậy: {option.confidence}
                    </div>
                  )}
                  {option.examples && option.examples.length > 0 && (
                    <div className="option-examples">
                      <strong>Ví dụ:</strong> {option.examples.join(", ")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      {!isUser && message.processing_time && (
        <div className="message-meta">
          <small>Thời gian xử lý: {message.processing_time.toFixed(2)}s</small>
        </div>
      )}

      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          <details>
            <summary>Nguồn tham khảo ({message.sources.length})</summary>
            <ul>
              {message.sources.map((source, index) => (
                <li key={index}>
                  {typeof source === "string" ? source : JSON.stringify(source)}
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
