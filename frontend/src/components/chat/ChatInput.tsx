import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Send } from "lucide-react";
import { VoiceInput } from "./VoiceInput";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleTranscriptChange = (transcript: string) => {
    setMessage(transcript);
  };

  const handleFinalTranscript = (transcript: string) => {
    setMessage(transcript);
    setIsListening(false);
  };

  const handleVoiceStart = () => {
    setIsListening(true);
    setMessage(""); // Xóa nội dung cũ khi bắt đầu ghi âm
  };

  const handleVoiceStop = () => {
    setIsListening(false);
  };

  const getVoiceStatusText = () => {
    if (!isListening) return "Nhập câu hỏi của bạn hoặc sử dụng microphone...";
    return "🎤 Đang lắng nghe... Hãy nói gì đó...";
  };

  return (
    <div className="chat-input-container">
      <div className="chat-input-layout">
        <form onSubmit={handleSubmit} className="chat-input-form">
          {/* Input Area */}
          <div className="chat-input-field-wrapper">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={getVoiceStatusText()}
              disabled={disabled}
              className={`chat-input-field ${
                isListening ? "chat-input-field--listening" : ""
              }`}
            />
            {isListening && (
              <div className="chat-input-recording-indicator">
                <div className="chat-input-recording-content">
                  <div className="chat-input-recording-dot"></div>
                  <span className="chat-input-recording-text">Đang ghi âm</span>
                </div>
              </div>
            )}
          </div>
          {/* Voice Input Button */}
          <VoiceInput
            onTranscriptChange={handleTranscriptChange}
            onFinalTranscript={handleFinalTranscript}
            onStart={handleVoiceStart}
            onStop={handleVoiceStop}
            disabled={disabled}
          />

          {/* Send Button */}
          <Button
            type="submit"
            disabled={!message.trim() || disabled}
            className="chat-input-send-button"
          >
            <Send className="chat-input-send-icon" />
          </Button>
        </form>
      </div>
    </div>
  );
}
