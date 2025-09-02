import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import SpeechControlsSimple from "../SpeechControlsSimple";
import logoHCC from "../../assets/LOGO_HCC.jpg";
import { User, FileText } from "lucide-react";

// Use Message from useChat hook since MainChatPage uses useChat
interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: string;
  clarification?: any;
  processingTime?: number;
  sourceDocuments?: string[];
  formAttachments?: any[];
  apiResponse?: any;
}

interface ChatMessageProps {
  message: Message;
  onClarificationClick?: (option: any) => void;
  logoSrc?: string;
}

export function ChatMessage({ message, logoSrc = logoHCC }: ChatMessageProps) {
  const isBot = message.isBot;

  const formatFileName = (filePath: string): string => {
    const fileName =
      filePath.split("\\").pop()?.replace(".json", "") || filePath;
    return fileName;
  };

  return (
    <div className="chat-message-container">
      <div className="chat-message-wrapper">
        {isBot ? (
          <div className="bot-message-layout">
            <Avatar className="message-avatar">
              <AvatarImage
                src={logoSrc}
                alt="Trợ lý AI"
                className="message-avatar-image"
              />
              <AvatarFallback className="message-avatar-fallback">
                AI
              </AvatarFallback>
            </Avatar>
            <div className="bot-message-content">
              <div className="bot-message-header">
                <span className="message-sender-name">Trợ lý AI</span>
                <span className="message-timestamp">{message.timestamp}</span>
                {message.processingTime && (
                  <span className="message-processing-time">
                    ({message.processingTime.toFixed(2)}s)
                  </span>
                )}
              </div>

              <div className="bot-message-bubble">
                <div className="message-text">{message.content}</div>
              </div>

              {message.sourceDocuments &&
                message.sourceDocuments.length > 0 && (
                  <div className="message-attachments">
                    <div className="attachments-header">
                      <FileText className="attachments-icon" />
                      <span>Tài liệu tham khảo:</span>
                    </div>
                    <div className="attachments-list">
                      {message.sourceDocuments.map(
                        (doc: string, index: number) => (
                          <div key={index} className="attachment-item">
                            <FileText className="attachment-icon" />
                            <span className="attachment-name">
                              {formatFileName(doc)}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}

              <div className="bot-message-actions">
                <SpeechControlsSimple text={message.content} />
              </div>
            </div>
          </div>
        ) : (
          <div className="user-message-layout">
            <div className="user-message-content">
              <div className="user-message-bubble">
                <div className="message-text">{message.content}</div>
              </div>
            </div>
            <Avatar className="message-avatar">
              <AvatarFallback className="message-avatar-fallback user-avatar">
                <User className="user-avatar-icon" />
              </AvatarFallback>
            </Avatar>
          </div>
        )}
      </div>
    </div>
  );
}
