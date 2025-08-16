import React from "react";
import { VoiceInput } from "../chat/VoiceInput";
import { Input } from "../ui/input";
import { Button } from "../ui/button";

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
    setTranscript("");
    setFinalTranscript("");
    setIsListening(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-8 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Demo Voice Input - Speech to Text
        </h1>
        <p className="text-gray-600">
          Nhấn vào nút microphone để bắt đầu nói. Hệ thống sẽ nhận dạng giọng
          nói của bạn thành văn bản.
        </p>
      </div>

      <div className="bg-white border-2 border-gray-200 rounded-2xl p-8 shadow-lg">
        <div className="flex items-center justify-center gap-6 mb-8">
          <VoiceInput
            onTranscriptChange={handleTranscriptChange}
            onFinalTranscript={handleFinalTranscript}
            onStart={handleStart}
            onStop={handleStop}
            className="scale-110"
          />
          <button
            onClick={clearAll}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors"
          >
            Xóa tất cả
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Real-time Transcript */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              📝 Văn bản theo thời gian thực
            </h3>
            <TranscriptDisplay
              transcript={transcript}
              isListening={isListening}
            />
          </div>

          {/* Final Transcript */}
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-3">
              ✅ Kết quả cuối cùng
            </h3>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 min-h-[100px]">
              {finalTranscript ? (
                <div className="text-gray-800 leading-relaxed">
                  {finalTranscript}
                </div>
              ) : (
                <div className="text-gray-400 italic">
                  Kết quả nhận dạng cuối cùng sẽ hiển thị ở đây...
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Status Information */}
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="font-medium text-blue-700">Trạng thái:</span>
              <span
                className={`ml-2 px-2 py-1 rounded ${
                  isListening
                    ? "bg-green-100 text-green-700"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {isListening ? "🎤 Đang lắng nghe" : "⏸️ Dừng"}
              </span>
            </div>
            <div>
              <span className="font-medium text-blue-700">Từ hiện tại:</span>
              <span className="ml-2 text-gray-700">
                {transcript.split(" ").filter((w) => w.trim()).length}
              </span>
            </div>
            <div>
              <span className="font-medium text-blue-700">Tổng từ:</span>
              <span className="ml-2 text-gray-700">
                {finalTranscript.split(" ").filter((w) => w.trim()).length}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-yellow-800 mb-3">
          🔧 Hướng dẫn sử dụng
        </h3>
        <ul className="space-y-2 text-yellow-700">
          <li>
            • <strong>Bước 1:</strong> Nhấn vào nút microphone để bắt đầu
          </li>
          <li>
            • <strong>Bước 2:</strong> Nói rõ ràng và tự nhiên
          </li>
          <li>
            • <strong>Bước 3:</strong> Nhấn lại nút microphone để dừng hoặc đợi
            3 giây
          </li>
          <li>
            • <strong>Lưu ý:</strong> Đảm bảo cho phép trình duyệt truy cập
            microphone
          </li>
        </ul>
      </div>
    </div>
  );
}
