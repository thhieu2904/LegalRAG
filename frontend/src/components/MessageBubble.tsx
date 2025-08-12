import React from "react";
import type { Message } from "../types/chat";

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.type === "user";

  return (
    <div className={`message-bubble ${isUser ? "user" : "assistant"}`}>
      <div className="message-header">
        <span className="message-type">{isUser ? "Bạn" : "Trợ lý"}</span>
        <span className="message-time">
          {message.timestamp.toLocaleTimeString()}
        </span>
      </div>

      <div className="message-content">{message.content}</div>

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
