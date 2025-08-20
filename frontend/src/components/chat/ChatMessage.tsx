import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import SpeechControlsSimple from "../SpeechControlsSimple";
import logoHCC from "../../assets/LOGO_HCC.jpg";
import { User } from "lucide-react";
import type {
  ClarificationData,
  ClarificationOption,
} from "../../services/chatService";
import { ClarificationOptions } from "./ClarificationOptions";

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: string;
  clarification?: ClarificationData;
  processingTime?: number;
  sourceDocuments?: string[];
  onClarificationSelect?: (option: ClarificationOption) => void;
}

export function ChatMessage({
  message,
  isBot,
  timestamp,
  clarification,
  processingTime,
  sourceDocuments,
  onClarificationSelect,
}: ChatMessageProps) {
  const formatFileName = (filePath: string): string => {
    const fileName =
      filePath.split("\\").pop()?.replace(".json", "") || filePath;
    return fileName;
  };

  return (
    <div className="chat-message-container">
      <div className="chat-message-wrapper">
        {isBot ? (
          // Bot message - căn trái
          <div className="bot-message-layout">
            <Avatar className="message-avatar">
              <AvatarImage
                src={logoHCC}
                alt="Trợ lý AI"
                className="bot-avatar-image"
              />
              <AvatarFallback className="bot-avatar-fallback">
                <img src={logoHCC} alt="AI" className="bot-avatar-logo" />
              </AvatarFallback>
            </Avatar>
            <div className="message-content-wrapper">
              <div className="message-header">
                <span className="bot-name">Trợ lý AI</span>
                <span className="message-timestamp">{timestamp}</span>
                {processingTime && (
                  <span className="processing-time">
                    ({processingTime.toFixed(2)}s)
                  </span>
                )}
              </div>

              <div className="bot-message-bubble">
                <div className="message-text">{message}</div>

                {/* Clarification Options */}
                {clarification && onClarificationSelect && (
                  <ClarificationOptions
                    clarification={clarification}
                    onOptionSelect={onClarificationSelect}
                  />
                )}
              </div>

              {/* Source Documents */}
              {sourceDocuments && sourceDocuments.length > 0 && (
                <div className="source-documents">
                  <div className="source-documents-label">
                    📄 Nguồn tài liệu tham khảo:
                  </div>
                  <div className="source-documents-list">
                    {sourceDocuments.map((doc, index) => (
                      <div key={index} className="source-document-item">
                        {formatFileName(doc)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Text-to-Speech Controls */}
              {isBot && (
                <div className="speech-controls-wrapper">
                  <SpeechControlsSimple text={message} />
                </div>
              )}
            </div>
          </div>
        ) : (
          // User message - căn phải
          <div className="user-message-layout">
            <div className="user-message-content">
              <div className="message-header user-header">
                <span className="message-timestamp">{timestamp}</span>
                <span className="user-name">Bạn</span>
              </div>

              <div className="user-message-bubble">
                <div className="message-text">{message}</div>
              </div>
            </div>
            <Avatar className="message-avatar">
              <AvatarFallback className="user-avatar-fallback">
                <User className="avatar-icon" />
              </AvatarFallback>
            </Avatar>
          </div>
        )}
      </div>
    </div>
  );
}
