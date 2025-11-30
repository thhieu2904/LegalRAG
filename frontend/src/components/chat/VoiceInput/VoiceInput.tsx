import { useEffect, useRef, useState } from 'react';
import { Mic, StopCircle } from 'lucide-react';
import styles from './VoiceInput.module.css';
import type { VoiceInputProps } from './VoiceInput.types';

// Minimal cross-browser typing for SpeechRecognition
interface SpeechRecognitionInstance {
  interimResults: boolean;
  continuous: boolean;
  lang?: string;
  start: () => void;
  stop: () => void;
  onresult?: (e: SpeechRecognitionEventLike) => void;
  onerror?: (e: unknown) => void;
  onend?: () => void;
}

type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

const getSpeechRecognition = (): SpeechRecognitionCtor | undefined => {
  const win = window as unknown as {
    webkitSpeechRecognition?: SpeechRecognitionCtor;
    SpeechRecognition?: SpeechRecognitionCtor;
  };
  return win.SpeechRecognition || win.webkitSpeechRecognition || undefined;
};

interface SpeechRecognitionResultItem {
  isFinal: boolean;
  0: { transcript: string };
}

interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: SpeechRecognitionResultItem[] & { length: number };
}

export const VoiceInput = ({
  onTranscriptChange,
  onFinalTranscript,
  onAutoSend,
  disabled,
  autoSend = false,
}: VoiceInputProps) => {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState<boolean | null>(null);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

  useEffect(() => {
    const SpeechRecognition = getSpeechRecognition();
    setSupported(Boolean(SpeechRecognition));

    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i] as SpeechRecognitionResultItem | undefined;
        if (!result) continue;
        const transcript = result[0]?.transcript || '';
        if (result.isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (onTranscriptChange) onTranscriptChange(interim);

      if (final) {
        // Final transcript
        if (onFinalTranscript) onFinalTranscript(final.trim());

        // Auto-send option
        (async () => {
          try {
            if (autoSend && onAutoSend) {
              await onAutoSend(final.trim());
            }
          } catch (err) {
            // Swallow errors; UI still usable
            console.error('autoSend failed:', err);
          }
        })();
      }
    };

    recognition.onerror = (e: unknown) => {
      console.warn('Speech recognition error', e);
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = undefined;
        recognitionRef.current.onerror = undefined;
        recognitionRef.current.onend = undefined;
        recognitionRef.current.stop?.();
        recognitionRef.current = null;
      }
    };
  }, [onTranscriptChange, onFinalTranscript, onAutoSend, autoSend]);

  const start = () => {
    if (disabled) return;
    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition || !recognitionRef.current) return;

    try {
      recognitionRef.current.lang = localStorage.getItem('voiceSettings')
        ? JSON.parse(localStorage.getItem('voiceSettings') || '{}')?.language || 'vi-VN'
        : 'vi-VN';
      recognitionRef.current.start();
      setListening(true);
      // noop
    } catch (err) {
      console.error('start recognition failed', err);
      setListening(false);
    }
  };

  const stop = () => {
    if (!recognitionRef.current) return;
    try {
      recognitionRef.current.stop?.();
      setListening(false);
      // noop
    } catch (err) {
      console.error('stop recognition failed', err);
    }
  };

  const toggle = () => {
    if (!supported) return;
    if (listening) stop();
    else start();
  };

  return (
    <div
      className={styles.voiceStatus}
      title={
        !supported
          ? 'Trình duyệt không hỗ trợ nhận dạng giọng nói'
          : listening
            ? 'Đang ghi âm...'
            : 'Ghi âm bằng giọng nói'
      }
    >
      <button
        type="button"
        onClick={toggle}
        className={`${styles.voiceButton} ${listening ? styles.listening : ''}`}
        disabled={disabled || supported === false}
        aria-pressed={listening}
        aria-disabled={disabled || supported === false}
      >
        {listening ? <StopCircle size={18} /> : <Mic size={18} />}
      </button>
      {listening && <div className={styles.pulse} aria-hidden />}
    </div>
  );
};
