import React, { useState } from "react";
import {
  textToSpeechService,
  type TextToSpeechConfig,
} from "../services/textToSpeech";
import SpeechControls from "./SpeechControls";
import { ContextInfoModal } from "./chat/ContextInfoModal";

interface AdminPanelProps {
  onBack: () => void;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ onBack }) => {
  const [config, setConfig] = useState<TextToSpeechConfig>({
    rate: 1.0,
    pitch: 1.0,
    volume: 0.8,
    lang: "vi-VN",
  });

  const [testText, setTestText] = useState(
    "Xin chào! Đây là ví dụ test giọng nói cho hệ thống Legal RAG Chat."
  );

  const handleConfigChange = (newConfig: Partial<TextToSpeechConfig>) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    textToSpeechService.updateConfig(updatedConfig);
  };

  const getAvailableVoices = () => {
    return textToSpeechService.getVietnameseVoices();
  };

  const resetToDefaults = () => {
    const defaultConfig = {
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8,
      lang: "vi-VN",
    };
    setConfig(defaultConfig);
    textToSpeechService.updateConfig(defaultConfig);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={onBack}
                className="text-gray-500 hover:text-gray-700 text-lg"
                title="Quay lại chat"
              >
                ←
              </button>
              <h1 className="text-2xl font-bold text-gray-900">
                ⚙️ Admin Panel
              </h1>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Text-to-Speech Settings */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            🔊 Cài đặt Text-to-Speech
          </h2>

          {/* System Info */}
          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">
              Thông tin hệ thống
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-blue-700 font-medium">Hỗ trợ TTS:</span>{" "}
                <span
                  className={
                    textToSpeechService.isSupported()
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  {textToSpeechService.isSupported() ? "✅ Có" : "❌ Không"}
                </span>
              </div>
              <div>
                <span className="text-blue-700 font-medium">Tổng giọng:</span>{" "}
                {textToSpeechService.getVoices().length}
              </div>
              <div>
                <span className="text-blue-700 font-medium">
                  Giọng tiếng Việt:
                </span>{" "}
                {textToSpeechService.getVietnameseVoices().length}
              </div>
            </div>
          </div>

          {/* Settings Controls */}
          <div className="space-y-6">
            {/* Speed */}
            <div className="space-y-2">
              <label className="block font-medium text-gray-700">
                Tốc độ đọc: {config.rate?.toFixed(1)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2.5"
                step="0.1"
                value={config.rate || 1}
                onChange={(e) =>
                  handleConfigChange({ rate: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0.5x</span>
                <span>Bình thường (1.0x)</span>
                <span>2.5x</span>
              </div>
            </div>

            {/* Pitch */}
            <div className="space-y-2">
              <label className="block font-medium text-gray-700">
                Cao độ giọng: {config.pitch?.toFixed(1)}
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={config.pitch || 1}
                onChange={(e) =>
                  handleConfigChange({ pitch: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Thấp (0.5)</span>
                <span>Bình thường (1.0)</span>
                <span>Cao (2.0)</span>
              </div>
            </div>

            {/* Volume */}
            <div className="space-y-2">
              <label className="block font-medium text-gray-700">
                Âm lượng: {Math.round((config.volume || 0.8) * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.volume || 0.8}
                onChange={(e) =>
                  handleConfigChange({ volume: parseFloat(e.target.value) })
                }
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Voice Selection */}
            <div className="space-y-2">
              <label className="block font-medium text-gray-700">
                Chọn giọng nói
              </label>
              <select
                value={config.voiceIndex || -1}
                onChange={(e) =>
                  handleConfigChange({ voiceIndex: parseInt(e.target.value) })
                }
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value={-1}>Mặc định (Tự động chọn)</option>
                {getAvailableVoices().map((voice, index) => (
                  <option key={voice.name} value={index}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={resetToDefaults}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                🔄 Đặt lại mặc định
              </button>
            </div>
          </div>

          {/* Test Area */}
          <div className="mt-8 p-4 bg-gray-50 rounded-lg">
            <h3 className="font-medium text-gray-900 mb-4">
              🧪 Test giọng nói
            </h3>
            <textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={3}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Nhập văn bản để test..."
            />
            <div className="mt-3">
              <SpeechControls text={testText} showAdvancedControls={false} />
            </div>
          </div>
        </div>

        {/* Context Information */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            📊 Thông tin Context & Session
          </h2>

          <div className="relative">
            <ContextInfoModal />
            <div className="text-gray-600 text-sm mt-4">
              Thông tin chi tiết về session hiện tại, context đang được sử dụng
              và các thông số liên quan.
            </div>
          </div>
        </div>

        {/* Usage Statistics */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
            📈 Thống kê sử dụng
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">0</div>
              <div className="text-sm text-green-700">Lần sử dụng TTS</div>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">0</div>
              <div className="text-sm text-blue-700">Session hoạt động</div>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">0</div>
              <div className="text-sm text-purple-700">Context đã tạo</div>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">0</div>
              <div className="text-sm text-orange-700">Errors</div>
            </div>
          </div>

          <div className="mt-4 text-xs text-gray-500">
            * Thống kê chỉ mang tính chất minh họa - có thể implement real
            tracking sau
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
