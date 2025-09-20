import React, { useState, useEffect } from "react";
import {
  textToSpeechService,
  type SpeechStatus,
  type TextToSpeechConfig,
} from "../../../services/textToSpeech";

interface SpeechControlsProps {
  text: string;
  className?: string;
  showAdvancedControls?: boolean;
}

const SpeechControls: React.FC<SpeechControlsProps> = ({
  text,
  className = "",
  showAdvancedControls = false,
}) => {
  const [speechStatus, setSpeechStatus] = useState<SpeechStatus>({
    isPlaying: false,
    isPaused: false,
    isSupported: textToSpeechService.isSupported(),
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const [config, setConfig] = useState<TextToSpeechConfig>({
    rate: 1.0,
    pitch: 1.0,
    volume: 0.8,
    lang: "vi-VN",
  });

  useEffect(() => {
    // Subscribe to speech status changes
    const unsubscribe = textToSpeechService.onStatusChange(setSpeechStatus);

    // Initial status
    setSpeechStatus(textToSpeechService.getStatus());

    return unsubscribe;
  }, []);

  const handlePlay = async () => {
    try {
      const cleanText = textToSpeechService.cleanTextForSpeech(text);
      if (cleanText.trim()) {
        await textToSpeechService.speak(cleanText);
      }
    } catch (error) {
      console.error("Lỗi khi phát âm thanh:", error);
      // Có thể hiển thị thông báo lỗi cho user
    }
  };

  const handlePause = () => {
    textToSpeechService.pause();
  };

  const handleResume = () => {
    textToSpeechService.resume();
  };

  const handleStop = () => {
    textToSpeechService.stop();
  };

  const handleConfigChange = (newConfig: Partial<TextToSpeechConfig>) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    textToSpeechService.updateConfig(updatedConfig);
  };

  const getAvailableVoices = () => {
    return textToSpeechService.getVietnameseVoices();
  };

  if (!speechStatus.isSupported) {
    return (
      <div className={`speech-controls speech-unsupported ${className}`}>
        <span className="speech-error">
          🔇 Trình duyệt không hỗ trợ đọc văn bản
        </span>
      </div>
    );
  }

  return (
    <div className={`speech-controls ${className}`}>
      <div className="speech-controls-main">
        {!speechStatus.isPlaying && (
          <button
            onClick={handlePlay}
            className="speech-btn speech-btn-play"
            title="Đọc văn bản"
            disabled={!text.trim()}
          >
            🔊
          </button>
        )}

        {speechStatus.isPlaying && !speechStatus.isPaused && (
          <button
            onClick={handlePause}
            className="speech-btn speech-btn-pause"
            title="Tạm dừng"
          >
            ⏸️
          </button>
        )}

        {speechStatus.isPlaying && speechStatus.isPaused && (
          <button
            onClick={handleResume}
            className="speech-btn speech-btn-resume"
            title="Tiếp tục"
          >
            ▶️
          </button>
        )}

        {speechStatus.isPlaying && (
          <button
            onClick={handleStop}
            className="speech-btn speech-btn-stop"
            title="Dừng"
          >
            ⏹️
          </button>
        )}

        {showAdvancedControls && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`speech-btn speech-btn-settings ${
              isExpanded ? "active" : ""
            }`}
            title="Cài đặt giọng nói"
          >
            ⚙️
          </button>
        )}
      </div>

      {showAdvancedControls && isExpanded && (
        <div className="speech-settings">
          <div className="speech-setting">
            <label>Tốc độ:</label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={config.rate || 1}
              onChange={(e) =>
                handleConfigChange({ rate: parseFloat(e.target.value) })
              }
            />
            <span>{config.rate?.toFixed(1)}x</span>
          </div>

          <div className="speech-setting">
            <label>Cao độ:</label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={config.pitch || 1}
              onChange={(e) =>
                handleConfigChange({ pitch: parseFloat(e.target.value) })
              }
            />
            <span>{config.pitch?.toFixed(1)}</span>
          </div>

          <div className="speech-setting">
            <label>Âm lượng:</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.volume || 0.8}
              onChange={(e) =>
                handleConfigChange({ volume: parseFloat(e.target.value) })
              }
            />
            <span>{Math.round((config.volume || 0.8) * 100)}%</span>
          </div>

          <div className="speech-setting">
            <label>Giọng nói:</label>
            <select
              value={config.voiceIndex || -1}
              onChange={(e) =>
                handleConfigChange({ voiceIndex: parseInt(e.target.value) })
              }
            >
              <option value={-1}>Mặc định</option>
              {getAvailableVoices().map((voice, index) => (
                <option key={voice.name} value={index}>
                  {voice.name} ({voice.lang})
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {speechStatus.isPlaying && speechStatus.currentText && (
        <div className="speech-status">
          <span className="speech-indicator">
            {speechStatus.isPaused ? "⏸️ Đã tạm dừng" : "🎵 Đang đọc..."}
          </span>
        </div>
      )}
    </div>
  );
};

export default SpeechControls;
