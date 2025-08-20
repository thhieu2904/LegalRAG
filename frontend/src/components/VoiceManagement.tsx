import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Slider } from "./ui/slider";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Mic,
  Volume2,
  Gauge,
  Music,
  Play,
  Pause,
  Square,
  RotateCcw,
} from "lucide-react";
import {
  textToSpeechService,
  type TextToSpeechConfig,
  type SpeechStatus,
} from "../services/textToSpeech";

export default function VoiceManagement() {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [config, setConfig] = useState<TextToSpeechConfig>({
    rate: 1.0,
    pitch: 1.0,
    volume: 0.8,
    lang: "vi-VN",
    voiceIndex: -1,
  });

  const [speechStatus, setSpeechStatus] = useState<SpeechStatus>({
    isPlaying: false,
    isPaused: false,
    isSupported: textToSpeechService.isSupported(),
  });

  const [testText, setTestText] = useState(
    "Xin chào! Đây là ví dụ test giọng nói cho hệ thống Legal RAG Chat. Trợ lý AI sẽ đọc các câu trả lời pháp luật một cách rõ ràng và tự nhiên."
  );
  const [availableVoices, setAvailableVoices] = useState<
    SpeechSynthesisVoice[]
  >([]);

  useEffect(() => {
    // Subscribe to speech status changes
    const unsubscribe = textToSpeechService.onStatusChange(setSpeechStatus);

    // Load available voices
    const loadVoices = () => {
      const voices = textToSpeechService.getVietnameseVoices();
      setAvailableVoices(voices);
    };

    loadVoices();

    // Listen for voices changed event
    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices;
    }

    // Initial status
    setSpeechStatus(textToSpeechService.getStatus());

    return () => {
      unsubscribe();
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  const handleConfigChange = (newConfig: Partial<TextToSpeechConfig>) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    textToSpeechService.updateConfig(updatedConfig);
  };

  const handleTestSpeech = async () => {
    if (speechStatus.isPlaying) {
      textToSpeechService.stop();
      return;
    }

    try {
      const cleanText = textToSpeechService.cleanTextForSpeech(testText);
      if (cleanText.trim()) {
        await textToSpeechService.speak(cleanText);
      }
    } catch (error) {
      console.error("Lỗi khi test giọng nói:", error);
    }
  };

  const handlePause = () => {
    if (speechStatus.isPaused) {
      textToSpeechService.resume();
    } else {
      textToSpeechService.pause();
    }
  };

  const resetToDefaults = () => {
    const defaultConfig = {
      rate: 1.0,
      pitch: 1.0,
      volume: 0.8,
      lang: "vi-VN",
      voiceIndex: -1,
    };
    setConfig(defaultConfig);
    textToSpeechService.updateConfig(defaultConfig);
  };

  const predefinedTexts = [
    "Xin chào! Tôi là trợ lý AI pháp luật của bạn.",
    "Theo Bộ luật Dân sự năm 2015, quyền sở hữu là quyền của chủ sở hữu đối với tài sản.",
    "Để được tư vấn pháp luật, bạn có thể đặt câu hỏi cụ thể về vấn đề của mình.",
    "Cảm ơn bạn đã sử dụng dịch vụ Legal RAG Chat!",
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-3">
        <Mic className="h-6 w-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-800">Cấu hình Giọng nói</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Text-to-Speech Configuration
          </CardTitle>
          <p className="text-sm text-gray-600">
            Quản lý các thông số giọng nói cho trợ lý AI
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Toggle chính */}
          <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                <Mic className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Chức năng Giọng nói</h3>
                <p className="text-sm text-gray-600">
                  {isVoiceEnabled ? "Đang hoạt động" : "Đã tắt"}
                </p>
              </div>
            </div>
            <Switch
              checked={isVoiceEnabled}
              onCheckedChange={setIsVoiceEnabled}
              className="data-[state=checked]:bg-blue-600"
            />
          </div>

          {/* Các slider điều chỉnh */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Tốc độ */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Gauge className="h-4 w-4 text-blue-600" />
                <Label className="font-medium">Tốc độ</Label>
              </div>
              <Slider
                value={[config.rate || 1.0]}
                onValueChange={(value) =>
                  handleConfigChange({ rate: value[0] })
                }
                min={0.5}
                max={2.5}
                step={0.1}
                className="w-full"
                disabled={!isVoiceEnabled}
              />
              <div className="flex justify-between text-sm text-gray-500">
                <span>0.5x</span>
                <span className="font-medium">
                  {(config.rate || 1.0).toFixed(1)}x
                </span>
                <span>2.5x</span>
              </div>
            </div>

            {/* Cao độ */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Music className="h-4 w-4 text-blue-600" />
                <Label className="font-medium">Cao độ</Label>
              </div>
              <Slider
                value={[config.pitch || 1.0]}
                onValueChange={(value) =>
                  handleConfigChange({ pitch: value[0] })
                }
                min={0.5}
                max={2.0}
                step={0.1}
                className="w-full"
                disabled={!isVoiceEnabled}
              />
              <div className="flex justify-between text-sm text-gray-500">
                <span>Thấp</span>
                <span className="font-medium">
                  {(config.pitch || 1.0).toFixed(1)}
                </span>
                <span>Cao</span>
              </div>
            </div>

            {/* Âm lượng */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Volume2 className="h-4 w-4 text-blue-600" />
                <Label className="font-medium">Âm lượng</Label>
              </div>
              <Slider
                value={[config.volume || 0.8]}
                onValueChange={(value) =>
                  handleConfigChange({ volume: value[0] })
                }
                min={0}
                max={1}
                step={0.1}
                className="w-full"
                disabled={!isVoiceEnabled}
              />
              <div className="flex justify-between text-sm text-gray-500">
                <span>0%</span>
                <span className="font-medium">
                  {Math.round((config.volume || 0.8) * 100)}%
                </span>
                <span>100%</span>
              </div>
            </div>
          </div>

          {/* Voice Selection */}
          <div className="space-y-3">
            <Label className="font-medium">Chọn giọng nói</Label>
            <Select
              value={config.voiceIndex?.toString() || "-1"}
              onValueChange={(value) =>
                handleConfigChange({ voiceIndex: parseInt(value) })
              }
              disabled={!isVoiceEnabled}
            >
              <SelectTrigger>
                <SelectValue placeholder="Chọn giọng nói" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="-1">Mặc định (Tự động)</SelectItem>
                {availableVoices.map((voice, index) => (
                  <SelectItem key={voice.name} value={index.toString()}>
                    {voice.name} ({voice.lang})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              Có {availableVoices.length} giọng nói khả dụng
            </p>
          </div>

          {/* System Info */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-2">Thông tin hệ thống</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Hỗ trợ TTS:</span>{" "}
                <span
                  className={
                    speechStatus.isSupported ? "text-green-600" : "text-red-600"
                  }
                >
                  {speechStatus.isSupported ? "✅ Có" : "❌ Không"}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Tổng giọng:</span>{" "}
                {textToSpeechService.getVoices().length}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              onClick={resetToDefaults}
              variant="outline"
              disabled={!isVoiceEnabled}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Đặt lại mặc định
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Test Area */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Test giọng nói</CardTitle>
          <p className="text-sm text-gray-600">
            Kiểm tra cài đặt giọng nói với văn bản mẫu
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Test Text Input */}
          <div className="space-y-2">
            <Label>Văn bản test</Label>
            <Textarea
              value={testText}
              onChange={(e) => setTestText(e.target.value)}
              rows={3}
              placeholder="Nhập văn bản để test giọng nói..."
              disabled={!isVoiceEnabled}
            />
          </div>

          {/* Test Controls */}
          <div className="flex items-center gap-3">
            <Button
              onClick={handleTestSpeech}
              disabled={
                !speechStatus.isSupported || !testText.trim() || !isVoiceEnabled
              }
              className={
                speechStatus.isPlaying ? "bg-red-600 hover:bg-red-700" : ""
              }
            >
              {speechStatus.isPlaying ? (
                <>
                  <Square className="h-4 w-4 mr-2" />
                  Dừng
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Phát
                </>
              )}
            </Button>

            {speechStatus.isPlaying && (
              <Button onClick={handlePause} variant="outline">
                <Pause className="h-4 w-4 mr-2" />
                {speechStatus.isPaused ? "Tiếp tục" : "Tạm dừng"}
              </Button>
            )}

            {speechStatus.isPlaying && (
              <div className="text-sm text-gray-600 flex items-center">
                🎵 {speechStatus.isPaused ? "Đã tạm dừng" : "Đang phát..."}
              </div>
            )}
          </div>

          {/* Predefined Test Texts */}
          <div className="space-y-2">
            <Label>Văn bản mẫu</Label>
            <div className="grid grid-cols-1 gap-2">
              {predefinedTexts.map((text, index) => (
                <Button
                  key={index}
                  variant="ghost"
                  className="text-left justify-start h-auto p-3 text-sm"
                  onClick={() => setTestText(text)}
                  disabled={!isVoiceEnabled}
                >
                  {text}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
