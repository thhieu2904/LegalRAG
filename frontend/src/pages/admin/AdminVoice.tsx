import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Switch } from "../../components/ui/switch";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Mic,
  Volume2,
  Gauge,
  Music,
  Play,
  Pause,
  Square,
  RotateCcw,
  Settings,
  Info,
} from "lucide-react";
import {
  textToSpeechService,
  type TextToSpeechConfig,
  type SpeechStatus,
} from "../../services/textToSpeech";
import { Alert, AlertDescription } from "../../components/ui/alert";

export default function AdminVoice() {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);
  const [isAutoSendEnabled, setIsAutoSendEnabled] = useState(false); // NEW: Auto-send feature
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

  // Save settings to localStorage
  const saveSettings = () => {
    localStorage.setItem(
      "voiceSettings",
      JSON.stringify({
        isVoiceEnabled,
        isAutoSendEnabled,
        config,
      })
    );
  };

  // Load settings from localStorage
  useEffect(() => {
    const savedSettings = localStorage.getItem("voiceSettings");
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings);
        setIsVoiceEnabled(settings.isVoiceEnabled ?? true);
        setIsAutoSendEnabled(settings.isAutoSendEnabled ?? false);
        if (settings.config) {
          setConfig(settings.config);
        }
      } catch (error) {
        console.log("Error loading voice settings:", error);
      }
    }
  }, []);

  // Update slider progress when config changes
  useEffect(() => {
    updateSliderProgress("rate", config.rate ?? 1.0);
    updateSliderProgress("pitch", config.pitch ?? 1.0);
    updateSliderProgress("volume", config.volume ?? 0.8);
  }, [config]);

  const handleConfigChange = (key: keyof TextToSpeechConfig, value: number) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    textToSpeechService.updateConfig(newConfig);

    // Update slider progress for visual feedback
    updateSliderProgress(key, value);
  };

  const updateSliderProgress = (key: string, value: number) => {
    let percentage = 0;
    switch (key) {
      case "rate":
        percentage = ((value - 0.5) / (2.0 - 0.5)) * 100;
        break;
      case "pitch":
        percentage = ((value - 0.5) / (2.0 - 0.5)) * 100;
        break;
      case "volume":
        percentage = (value / 1.0) * 100;
        break;
    }

    // Update CSS custom property for this slider
    const sliders = document.querySelectorAll(`input[type="range"]`);
    sliders.forEach((slider) => {
      const inputElement = slider as HTMLInputElement;
      if (inputElement.getAttribute("data-config") === key) {
        inputElement.style.setProperty("--slider-progress", `${percentage}%`);
      }
    });
  };

  const handleTestSpeech = async () => {
    if (!testText.trim()) return;

    try {
      await textToSpeechService.speak(testText);
    } catch (error) {
      console.error("Test speech error:", error);
    }
  };

  const handleStopSpeech = () => {
    textToSpeechService.stop();
  };

  const handlePauseSpeech = () => {
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
    setIsVoiceEnabled(true);
    setIsAutoSendEnabled(false);
    textToSpeechService.updateConfig(defaultConfig);
  };

  return (
    <div className="admin-page-container admin-voice-page">
      <div className="admin-page-header-section">
        <div className="admin-page-header-content">
          <h1 className="admin-page-title-main">Quản lý Giọng nói</h1>
          <p className="admin-page-subtitle-main">
            Cấu hình và quản lý tính năng Text-to-Speech của hệ thống
          </p>
        </div>
        <div className="admin-page-actions-main">
          <Button
            onClick={saveSettings}
            className="shared-button shared-button-primary"
          >
            <Settings className="w-4 h-4" />
            Lưu cài đặt
          </Button>
          <Button
            onClick={resetToDefaults}
            variant="outline"
            className="shared-button"
          >
            <RotateCcw className="w-4 h-4" />
            Đặt lại mặc định
          </Button>
        </div>
      </div>

      <div className="admin-content-section">
        <Alert className="voice-info-alert">
          <Info className="w-4 h-4" />
          <AlertDescription>
            <strong>Hướng dẫn:</strong> Cấu hình này áp dụng cho toàn bộ hệ
            thống. Tính năng tự động gửi cho phép người dùng gửi tin nhắn ngay
            sau khi nhận diện giọng nói mà không cần nhấn nút gửi.
          </AlertDescription>
        </Alert>
      </div>

      {/* Main Voice Configuration */}
      <div className="admin-content-section">
        <Card className="voice-config-card">
          <CardHeader className="voice-config-header">
            <div className="voice-config-title-section">
              <Mic className="voice-config-icon" />
              <div>
                <CardTitle className="voice-config-title">
                  Cấu hình Giọng nói
                </CardTitle>
                <p className="voice-config-subtitle">
                  Quản lý các thông số giọng nói cho trợ lý AI
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="voice-config-content">
            {/* Voice Enable Toggle */}
            <div className="voice-setting-group">
              <div className="voice-setting-header">
                <Label htmlFor="voice-enabled" className="voice-setting-label">
                  Chức năng Giọng nói
                </Label>
                <Switch
                  id="voice-enabled"
                  checked={isVoiceEnabled}
                  onCheckedChange={setIsVoiceEnabled}
                  className="voice-setting-switch"
                />
              </div>
              <p className="voice-setting-description">
                {isVoiceEnabled ? "Đang hoạt động" : "Đã tắt"}
              </p>
            </div>

            {/* NEW: Auto Send Toggle */}
            <div className="voice-setting-group">
              <div className="voice-setting-header">
                <Label
                  htmlFor="auto-send-enabled"
                  className="voice-setting-label"
                >
                  Tự động gửi tin nhắn
                </Label>
                <Switch
                  id="auto-send-enabled"
                  checked={isAutoSendEnabled}
                  onCheckedChange={setIsAutoSendEnabled}
                  className="voice-setting-switch"
                />
              </div>
              <p className="voice-setting-description">
                {isAutoSendEnabled
                  ? "Tự động gửi tin nhắn sau khi nhận diện giọng nói"
                  : "Cần nhấn nút gửi sau khi nhận diện giọng nói"}
              </p>
            </div>

            {/* Voice Controls - Improved Sliders */}
            <div className="voice-controls-grid">
              {/* Speed Control */}
              <div className="voice-control-item">
                <div className="voice-control-header">
                  <Gauge className="voice-control-icon" />
                  <Label className="voice-control-label">Tốc độ</Label>
                </div>
                <div className="voice-slider-container">
                  <div className="voice-slider-wrapper">
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={config.rate}
                      data-config="rate"
                      onChange={(e) =>
                        handleConfigChange("rate", parseFloat(e.target.value))
                      }
                      className="voice-slider"
                    />
                  </div>
                  <div className="voice-slider-labels">
                    <span className="voice-slider-min">0.5x</span>
                    <span className="voice-slider-current">
                      {(config.rate ?? 1.0).toFixed(1)}x
                    </span>
                    <span className="voice-slider-max">2.0x</span>
                  </div>
                </div>
              </div>

              {/* Pitch Control */}
              <div className="voice-control-item">
                <div className="voice-control-header">
                  <Music className="voice-control-icon" />
                  <Label className="voice-control-label">Cao độ</Label>
                </div>
                <div className="voice-slider-container">
                  <div className="voice-slider-wrapper">
                    <input
                      type="range"
                      min="0.5"
                      max="2.0"
                      step="0.1"
                      value={config.pitch}
                      data-config="pitch"
                      onChange={(e) =>
                        handleConfigChange("pitch", parseFloat(e.target.value))
                      }
                      className="voice-slider"
                    />
                  </div>
                  <div className="voice-slider-labels">
                    <span className="voice-slider-min">Thấp</span>
                    <span className="voice-slider-current">
                      {(config.pitch ?? 1.0).toFixed(1)}
                    </span>
                    <span className="voice-slider-max">Cao</span>
                  </div>
                </div>
              </div>

              {/* Volume Control */}
              <div className="voice-control-item">
                <div className="voice-control-header">
                  <Volume2 className="voice-control-icon" />
                  <Label className="voice-control-label">Âm lượng</Label>
                </div>
                <div className="voice-slider-container">
                  <div className="voice-slider-wrapper">
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={config.volume}
                      data-config="volume"
                      onChange={(e) =>
                        handleConfigChange("volume", parseFloat(e.target.value))
                      }
                      className="voice-slider"
                    />
                  </div>
                  <div className="voice-slider-labels">
                    <span className="voice-slider-min">0%</span>
                    <span className="voice-slider-current">
                      {Math.round((config.volume ?? 0.8) * 100)}%
                    </span>
                    <span className="voice-slider-max">100%</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Voice Selection - Fixed Dropdown */}
            <div className="voice-setting-group">
              <Label className="voice-setting-label">Chọn giọng nói</Label>
              <Select
                value={(config.voiceIndex ?? -1).toString()}
                onValueChange={(value) =>
                  handleConfigChange("voiceIndex", parseInt(value))
                }
              >
                <SelectTrigger className="w-full h-12 text-sm">
                  <SelectValue placeholder="Mặc định (Tự động)" />
                </SelectTrigger>
                <SelectContent className="z-50 max-h-[300px] overflow-y-auto">
                  <SelectItem value="-1">Mặc định (Tự động)</SelectItem>
                  {availableVoices.map((voice, index) => (
                    <SelectItem key={index} value={index.toString()}>
                      <div className="flex justify-between items-center w-full">
                        <span className="font-medium">{voice.name}</span>
                        <span className="text-xs text-muted-foreground ml-2 bg-muted px-2 py-1 rounded">
                          {voice.lang}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-2 italic">
                Có {availableVoices.length} giọng nói khả dụng
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Test Voice Section */}
      <div className="admin-content-section">
        <Card className="voice-test-card">
          <CardHeader>
            <CardTitle className="voice-test-title">Test giọng nói</CardTitle>
            <p className="voice-test-subtitle">
              Kiểm tra cài đặt giọng nói với văn bản mẫu
            </p>
          </CardHeader>
          <CardContent className="voice-test-content">
            <div className="voice-test-input-group">
              <Label htmlFor="test-text" className="voice-test-label">
                Văn bản test
              </Label>
              <Textarea
                id="test-text"
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
                className="voice-test-textarea"
                placeholder="Nhập văn bản để test giọng nói..."
                rows={3}
              />
            </div>

            <div className="voice-test-controls">
              <Button
                onClick={handleTestSpeech}
                disabled={
                  !speechStatus.isSupported ||
                  !testText.trim() ||
                  speechStatus.isPlaying
                }
                className="shared-button shared-button-primary"
              >
                <Play className="w-4 h-4" />
                {speechStatus.isPlaying ? "Đang phát..." : "Test giọng nói"}
              </Button>

              {speechStatus.isPlaying && (
                <Button
                  onClick={handlePauseSpeech}
                  variant="outline"
                  className="shared-button"
                >
                  {speechStatus.isPaused ? (
                    <Play className="w-4 h-4" />
                  ) : (
                    <Pause className="w-4 h-4" />
                  )}
                  {speechStatus.isPaused ? "Tiếp tục" : "Tạm dừng"}
                </Button>
              )}

              {speechStatus.isPlaying && (
                <Button
                  onClick={handleStopSpeech}
                  variant="outline"
                  className="shared-button"
                >
                  <Square className="w-4 h-4" />
                  Dừng
                </Button>
              )}
            </div>

            {/* System Info */}
            <div className="voice-system-info">
              <div className="voice-info-grid">
                <div className="voice-info-item">
                  <span className="voice-info-label">Hỗ trợ TTS:</span>
                  <span
                    className={`voice-info-value ${
                      speechStatus.isSupported
                        ? "voice-info-success"
                        : "voice-info-error"
                    }`}
                  >
                    {speechStatus.isSupported ? "✓ Có" : "✗ Không"}
                  </span>
                </div>
                <div className="voice-info-item">
                  <span className="voice-info-label">Tổng giọng:</span>
                  <span className="voice-info-value">
                    {availableVoices.length}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
