import { useEffect, useState } from "react";

interface TranscriptDisplayProps {
  transcript: string;
  isListening: boolean;
  className?: string;
}

export function TranscriptDisplay({
  transcript,
  isListening,
  className = "",
}: TranscriptDisplayProps) {
  const [displayedText, setDisplayedText] = useState("");

  // Hiệu ứng typing cho transcript
  useEffect(() => {
    if (transcript.length === 0) {
      setDisplayedText("");
      return;
    }

    // Nếu transcript mới dài hơn, chỉ thêm phần mới
    if (transcript.length > displayedText.length) {
      let currentIndex = displayedText.length;
      const interval = setInterval(() => {
        currentIndex++;
        if (currentIndex <= transcript.length) {
          setDisplayedText(transcript.slice(0, currentIndex));
        } else {
          clearInterval(interval);
        }
      }, 50); // Tốc độ gõ

      return () => clearInterval(interval);
    } else {
      // Nếu transcript mới ngắn hơn (được reset), reset display
      setDisplayedText(transcript);
    }
  }, [transcript, displayedText.length]);

  if (!isListening && !transcript) {
    return null;
  }

  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-4 shadow-sm ${className}`}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="flex items-center gap-1">
          {isListening && (
            <>
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600 font-medium">
                Đang ghi âm
              </span>
            </>
          )}
          {!isListening && transcript && (
            <>
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-green-600 font-medium">
                Hoàn thành
              </span>
            </>
          )}
        </div>
      </div>

      <div className="min-h-[60px]">
        {isListening && !transcript && (
          <div className="text-gray-400 italic">Hãy nói gì đó...</div>
        )}

        {displayedText && (
          <div className="text-gray-800 leading-relaxed">
            {displayedText}
            {isListening && (
              <span className="inline-block w-0.5 h-5 bg-blue-500 ml-1 animate-pulse"></span>
            )}
          </div>
        )}
      </div>

      {transcript && !isListening && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            📝 Đã nhận dạng {transcript.split(" ").length} từ
          </div>
        </div>
      )}
    </div>
  );
}
