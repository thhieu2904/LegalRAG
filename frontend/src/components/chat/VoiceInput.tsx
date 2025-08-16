import { useState, useEffect, useRef } from "react";
import { Button } from "../ui/button";
import { Mic, MicOff } from "lucide-react";

interface VoiceInputProps {
  onTranscriptChange: (transcript: string) => void;
  onFinalTranscript: (transcript: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  disabled?: boolean;
  className?: string;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionResult {
  readonly isFinal: boolean;
  readonly [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  readonly [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  grammars: unknown;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  serviceURI: string;
  start(): void;
  stop(): void;
  abort(): void;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onaudioend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onerror: ((this: SpeechRecognition, ev: Event) => void) | null;
  onnomatch: ((this: SpeechRecognition, ev: Event) => void) | null;
  onresult:
    | ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void)
    | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => void) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => void) | null;
  onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

type RecordingState = "idle" | "listening" | "speaking" | "processing";

export function VoiceInput({
  onTranscriptChange,
  onFinalTranscript,
  onStart,
  onStop,
  disabled = false,
  className = "",
}: VoiceInputProps) {
  const [recordingState, setRecordingState] = useState<RecordingState>("idle");
  const [isSupported, setIsSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const timeoutRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  // Kiểm tra browser support
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      setError("Trình duyệt không hỗ trợ nhận dạng giọng nói");
    }
  }, []);

  // Cleanup khi component unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Thiết lập audio analyzer để phát hiện giọng nói
  const setupAudioAnalyzer = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);

      analyserRef.current.fftSize = 256;
      const bufferLength = analyserRef.current.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const checkAudioLevel = () => {
        if (analyserRef.current && recordingState !== "idle") {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;

          // Phát hiện có giọng nói (ngưỡng có thể điều chỉnh)
          if (average > 20) {
            setRecordingState("speaking");
          } else {
            setRecordingState("listening");
          }

          animationRef.current = requestAnimationFrame(checkAudioLevel);
        }
      };

      checkAudioLevel();
    } catch (err) {
      console.warn("Không thể truy cập microphone để phân tích âm thanh:", err);
      // Vẫn tiếp tục với speech recognition mà không có audio analysis
    }
  };

  const startRecording = async () => {
    if (!isSupported || disabled) return;

    try {
      setError(null);

      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();

      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = "vi-VN"; // Thiết lập tiếng Việt
      recognitionRef.current.maxAlternatives = 1;

      recognitionRef.current.onstart = () => {
        setRecordingState("listening");
        onStart?.();
        setupAudioAnalyzer();
      };

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        let interimText = "";
        let finalText = "";

        // Chỉ lấy kết quả từ session hiện tại, không lưu trữ transcript cũ
        for (let i = 0; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalText += result[0].transcript;
          } else {
            interimText += result[0].transcript;
          }
        }

        // Gửi transcript hiện tại (chỉ từ session này)
        const currentTranscript = finalText + interimText;
        onTranscriptChange(currentTranscript);

        if (finalText) {
          onFinalTranscript(finalText);
        }

        // Reset timeout để tự động dừng sau khi không có giọng nói
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
        }
        timeoutRef.current = setTimeout(() => {
          stopRecording();
        }, 2000); // Dừng sau 2 giây không có giọng nói
      };

      recognitionRef.current.onerror = (event: Event & { error?: string }) => {
        console.warn("Speech recognition error:", event.error);
        const errorMsg = event.error;

        // Chỉ hiển thị lỗi quan trọng, bỏ qua một số lỗi thông thường
        if (errorMsg && !["no-speech", "aborted"].includes(errorMsg)) {
          setError(`Lỗi nhận dạng giọng nói: ${errorMsg}`);
        }

        setRecordingState("idle");
      };

      recognitionRef.current.onend = () => {
        setRecordingState("idle");
        onStop?.();
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };

      recognitionRef.current.start();
    } catch (err) {
      console.error("Lỗi khi bắt đầu recording:", err);
      setError("Không thể bắt đầu ghi âm");
      setRecordingState("idle");
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setRecordingState("idle");
  };

  const toggleRecording = () => {
    if (recordingState === "idle") {
      startRecording();
    } else {
      stopRecording();
    }
  };

  const getButtonStyle = () => {
    switch (recordingState) {
      case "listening":
        return "bg-green-50 hover:bg-green-100 border-2 border-green-300 shadow-lg animate-pulse";
      case "speaking":
        return "bg-blue-50 hover:bg-blue-100 border-2 border-blue-400 shadow-xl animate-bounce";
      case "processing":
        return "bg-yellow-50 hover:bg-yellow-100 border-2 border-yellow-300 shadow-lg";
      default:
        return "bg-blue-50 hover:bg-blue-100 border-2 border-blue-200 hover:border-blue-300";
    }
  };

  const getIconColor = () => {
    switch (recordingState) {
      case "listening":
        return "text-green-600";
      case "speaking":
        return "text-blue-600";
      case "processing":
        return "text-yellow-600";
      default:
        return "text-blue-600";
    }
  };

  if (!isSupported) {
    return (
      <Button
        type="button"
        variant="outline"
        disabled={true}
        className={`h-14 w-14 p-0 bg-gray-50 border-2 border-gray-200 rounded-xl ${className}`}
        title="Trình duyệt không hỗ trợ nhận dạng giọng nói"
      >
        <MicOff className="w-7 h-7 text-gray-400" />
      </Button>
    );
  }

  return (
    <div className="relative">
      <Button
        type="button"
        variant="outline"
        disabled={disabled}
        onClick={toggleRecording}
        className={`h-14 w-14 p-0 rounded-xl transition-all duration-200 hover:scale-105 ${getButtonStyle()} ${className}`}
        title={
          recordingState === "idle"
            ? "Nhấn để bắt đầu nói"
            : recordingState === "listening"
            ? "Đang lắng nghe..."
            : recordingState === "speaking"
            ? "Đang ghi âm giọng nói..."
            : "Đang xử lý..."
        }
      >
        <div className="relative">
          <Mic className={`w-7 h-7 ${getIconColor()}`} />

          {/* Hiệu ứng sóng âm khi đang lắng nghe */}
          {recordingState === "listening" && (
            <>
              <div className="absolute inset-0 rounded-full border-2 border-green-400 animate-ping opacity-75"></div>
              <div className="absolute inset-0 rounded-full border border-green-300 animate-pulse"></div>
            </>
          )}

          {/* Hiệu ứng khi đang nói */}
          {recordingState === "speaking" && (
            <>
              <div className="absolute inset-0 rounded-full bg-blue-400 animate-ping opacity-30"></div>
              <div className="absolute inset-0 rounded-full border-2 border-blue-500 animate-pulse"></div>
            </>
          )}
        </div>
      </Button>

      {/* Hiển thị trạng thái */}
      {recordingState !== "idle" && (
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-xs font-medium whitespace-nowrap">
          {recordingState === "listening" && (
            <span className="text-green-600">🎤 Đang lắng nghe...</span>
          )}
          {recordingState === "speaking" && (
            <span className="text-blue-600">🔵 Đang ghi âm...</span>
          )}
          {recordingState === "processing" && (
            <span className="text-yellow-600">⚡ Đang xử lý...</span>
          )}
        </div>
      )}

      {/* Hiển thị lỗi */}
      {error && (
        <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 text-xs text-red-600 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  );
}
