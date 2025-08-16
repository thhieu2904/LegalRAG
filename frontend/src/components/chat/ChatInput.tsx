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
    <div className="p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <form onSubmit={handleSubmit} className="flex gap-4 items-end">
          {/* Input Area */}
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={getVoiceStatusText()}
              disabled={disabled}
              className={`h-14 text-base border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-xl px-4 ${
                isListening ? "bg-green-50 border-green-300" : ""
              }`}
            />
            {isListening && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="flex items-center gap-2 text-green-600">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium">Đang ghi âm</span>
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
            className="bg-blue-600 hover:bg-blue-700 h-14 w-14 p-0 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all duration-200 hover:scale-105"
          >
            <Send className="w-6 h-6" />
          </Button>
        </form>
      </div>
    </div>
  );
}
