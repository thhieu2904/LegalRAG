import React from "react";
import { VoiceInput } from "../chat/VoiceInput";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Send, Trash2 } from "lucide-react";

export function VoiceInputDemo() {
  const [message, setMessage] = React.useState("");
  const [isListening, setIsListening] = React.useState(false);
  const [history, setHistory] = React.useState<string[]>([]);

  const handleTranscriptChange = (newTranscript: string) => {
    setMessage(newTranscript);
    console.log("Transcript change:", newTranscript);
  };

  const handleFinalTranscript = (newTranscript: string) => {
    setMessage(newTranscript);
    console.log("Final transcript:", newTranscript);
  };

  const handleStart = () => {
    setIsListening(true);
    setMessage(""); // Xóa nội dung cũ khi bắt đầu ghi âm
    console.log("Voice input started");
  };

  const handleStop = () => {
    setIsListening(false);
    console.log("Voice input stopped");
  };

  const handleSend = () => {
    if (message.trim()) {
      setHistory((prev) => [...prev, message.trim()]);
      setMessage("");
    }
  };

  const clearAll = () => {
    setMessage("");
    setHistory([]);
  };

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          🎤 Demo Voice Input - Speech to Text
        </h1>
        <p className="text-gray-600">
          Nhấn vào nút microphone để bắt đầu nói. Văn bản sẽ xuất hiện trực tiếp
          trong ô nhập liệu.
        </p>
      </div>

      {/* Main Input Area */}
      <div className="bg-white border-2 border-gray-200 rounded-2xl p-6 shadow-lg">
        <div className="flex gap-4 items-end mb-6">
          {/* Voice Input Button */}
          <VoiceInput
            onTranscriptChange={handleTranscriptChange}
            onFinalTranscript={handleFinalTranscript}
            onStart={handleStart}
            onStop={handleStop}
            className="scale-110"
          />

          {/* Input Field */}
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={
                isListening
                  ? "🎤 Đang lắng nghe... Hãy nói gì đó..."
                  : "Nhập văn bản hoặc sử dụng microphone..."
              }
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

          {/* Send Button */}
          <Button
            onClick={handleSend}
            disabled={!message.trim()}
            className="bg-blue-600 hover:bg-blue-700 h-14 w-14 p-0 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all duration-200 hover:scale-105"
          >
            <Send className="w-6 h-6" />
          </Button>

          {/* Clear Button */}
          <Button
            onClick={clearAll}
            variant="outline"
            className="h-14 w-14 p-0 border-2 border-gray-200 hover:border-red-300 hover:bg-red-50 rounded-xl transition-all duration-200"
          >
            <Trash2 className="w-6 h-6 text-gray-600 hover:text-red-600" />
          </Button>
        </div>

        {/* Status */}
        <div className="text-center">
          {isListening && (
            <div className="text-green-600 font-medium">
              🎤 Đang lắng nghe... Hãy nói để văn bản xuất hiện trong ô nhập
              liệu
            </div>
          )}
          {!isListening && message && (
            <div className="text-blue-600 font-medium">
              ✅ Đã nhận dạng được{" "}
              {message.split(" ").filter((w) => w.trim()).length} từ
            </div>
          )}
          {!isListening && !message && (
            <div className="text-gray-500">
              Nhấn microphone để bắt đầu hoặc gõ trực tiếp
            </div>
          )}
        </div>
      </div>

      {/* History */}
      {history.length > 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            📝 Lịch sử văn bản đã gửi
          </h3>
          <div className="space-y-3">
            {history.map((text, index) => (
              <div
                key={index}
                className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm"
              >
                <div className="text-sm text-gray-500 mb-1">
                  Tin nhắn #{index + 1}
                </div>
                <div className="text-gray-800">{text}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-3">
          📋 Hướng dẫn sử dụng
        </h3>
        <ul className="space-y-2 text-blue-700">
          <li>
            • <strong>Nhấn microphone:</strong> Bắt đầu ghi âm (nội dung cũ sẽ
            bị xóa)
          </li>
          <li>
            • <strong>Nói:</strong> Văn bản sẽ xuất hiện trực tiếp trong ô nhập
            liệu
          </li>
          <li>
            • <strong>Hoạt động offline:</strong> Sử dụng Web Speech API có sẵn
            trong trình duyệt
          </li>
          <li>
            • <strong>Tự động dừng:</strong> Sau 2 giây không có giọng nói
          </li>
          <li>
            • <strong>Hỗ trợ tiếng Việt:</strong> Đã được cấu hình cho tiếng
            Việt
          </li>
        </ul>
      </div>
    </div>
  );
}
