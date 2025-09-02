import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import SpeechControlsSimple from "../SpeechControlsSimple";
import logoHCC from "../../assets/LOGO_HCC.jpg";
import { User, Download, FileText } from "lucide-react";
import type {
  ClarificationData,
  ClarificationOption,
} from "../../services/chatService";
import { ClarificationOptions } from "./ClarificationOptions";

interface FormAttachment {
  document_id: string;
  document_title: string;
  form_filename: string;
  form_url: string;
  collection_id: string;
}

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: string;
  clarification?: ClarificationData;
  processingTime?: number;
  sourceDocuments?: string[];
  formAttachments?: FormAttachment[]; // NEW: Form attachments
  onClarificationSelect?: (option: ClarificationOption) => void;
}

export function ChatMessage({
  message,
  isBot,
  timestamp,
  clarification,
  processingTime,
  sourceDocuments,
  formAttachments,
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

              {/* Combined Attachments - Nguồn tham khảo và Biểu mẫu */}
              {((sourceDocuments && sourceDocuments.length > 0) ||
                (formAttachments && formAttachments.length > 0)) && (
                <div className="attachments-section">
                  <div className="attachments-header">
                    📎 Tệp đính kèm & Tài liệu tham khảo
                  </div>

                  <div className="attachments-rows">
                    {/* Source Documents Row */}
                    {sourceDocuments && sourceDocuments.length > 0 && (
                      <div className="attachments-row source-documents-row">
                        <div className="row-title">📄 Nguồn tham khảo</div>
                        <div className="attachments-list source-documents-list">
                          {sourceDocuments.map((doc, index) => (
                            <div
                              key={index}
                              className="attachment-item source-item"
                            >
                              <FileText size={14} className="attachment-icon" />
                              <span className="attachment-name">
                                {formatFileName(doc)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Form Attachments Row */}
                    {formAttachments && formAttachments.length > 0 && (
                      <div className="attachments-row forms-row">
                        <div className="row-title">📋 Biểu mẫu/Tờ khai</div>
                        <div className="attachments-list form-attachments-list">
                          {formAttachments.map((form, index) => (
                            <div
                              key={index}
                              className="attachment-item form-item"
                            >
                              <div className="form-info">
                                <FileText
                                  size={14}
                                  className="attachment-icon"
                                />
                                <div className="form-details">
                                  <span className="form-document-title">
                                    {form.document_title}
                                  </span>
                                  <span className="form-filename">
                                    {form.form_filename}
                                  </span>
                                </div>
                              </div>
                              <a
                                href={form.form_url}
                                download={form.form_filename}
                                className="download-button"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Download size={12} />
                                Tải về
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
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
