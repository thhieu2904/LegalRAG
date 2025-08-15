import { useState } from "react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Send, Mic } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSendMessage, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        <form onSubmit={handleSubmit} className="flex gap-4 items-end">
          {/* Mic Button - Standalone và nổi bật */}

          {/* Input Area */}
          <div className="flex-1">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Nhập câu hỏi của bạn..."
              disabled={disabled}
              className="h-14 text-base border-gray-300 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 rounded-xl px-4"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            disabled={disabled}
            className="h-14 w-14 p-0 bg-blue-50 hover:bg-blue-100 border-2 border-blue-200 hover:border-blue-300 rounded-xl transition-all duration-200 hover:scale-105 shadow-md hover:shadow-lg"
          >
            <Mic className="w-7 h-7 text-blue-600" />
          </Button>
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
