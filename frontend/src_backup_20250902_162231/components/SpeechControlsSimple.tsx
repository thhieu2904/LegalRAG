import React, { useState, useEffect } from "react";
import {
  textToSpeechService,
  type SpeechStatus,
} from "../services/textToSpeech";

interface SpeechControlsSimpleProps {
  text: string;
  className?: string;
}

const SpeechControlsSimple: React.FC<SpeechControlsSimpleProps> = ({
  text,
  className = "",
}) => {
  const [speechStatus, setSpeechStatus] = useState<SpeechStatus>({
    isPlaying: false,
    isPaused: false,
    isSupported: textToSpeechService.isSupported(),
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

  if (!speechStatus.isSupported) {
    return null; // Không hiển thị gì nếu không hỗ trợ
  }

  return (
    <div className={`simple-speech-controls ${className}`}>
      <div className="flex items-center gap-1">
        {!speechStatus.isPlaying && (
          <button
            onClick={handlePlay}
            className="simple-speech-btn simple-speech-btn-play"
            title="Đọc văn bản"
            disabled={!text.trim()}
          >
            🔊
          </button>
        )}

        {speechStatus.isPlaying && !speechStatus.isPaused && (
          <button
            onClick={handlePause}
            className="simple-speech-btn simple-speech-btn-pause"
            title="Tạm dừng"
          >
            ⏸️
          </button>
        )}

        {speechStatus.isPlaying && speechStatus.isPaused && (
          <button
            onClick={handleResume}
            className="simple-speech-btn simple-speech-btn-resume"
            title="Tiếp tục"
          >
            ▶️
          </button>
        )}

        {speechStatus.isPlaying && (
          <button
            onClick={handleStop}
            className="simple-speech-btn simple-speech-btn-stop"
            title="Dừng"
          >
            ⏹️
          </button>
        )}

        {speechStatus.isPlaying && (
          <span className="simple-speech-indicator">
            {speechStatus.isPaused ? "⏸️" : "🎵"}
          </span>
        )}
      </div>
    </div>
  );
};

export default SpeechControlsSimple;
