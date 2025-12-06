import { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, StopCircle } from 'lucide-react';
import styles from './VoiceInput.module.css';
import type { VoiceInputProps } from './VoiceInput.types';

// Cross-browser SpeechRecognition
interface SpeechRecognitionInstance {
  interimResults: boolean;
  continuous: boolean;
  lang?: string;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult?: (e: SpeechRecognitionEventLike) => void;
  onerror?: (e: { error: string }) => void;
  onend?: () => void;
}

type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

const getSpeechRecognition = (): SpeechRecognitionCtor | undefined => {
  const win = window as unknown as {
    webkitSpeechRecognition?: SpeechRecognitionCtor;
    SpeechRecognition?: SpeechRecognitionCtor;
  };
  return win.SpeechRecognition || win.webkitSpeechRecognition;
};

interface SpeechRecognitionResultItem {
  isFinal: boolean;
  0: { transcript: string };
}

interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: SpeechRecognitionResultItem[] & { length: number };
}

const getVoiceSettings = () => {
  try {
    const raw = localStorage.getItem('voiceSettings');
    if (!raw) return { language: 'vi-VN', isAutoSendEnabled: false };
    const parsed = JSON.parse(raw);
    return {
      language: parsed.language || 'vi-VN',
      isAutoSendEnabled: Boolean(parsed.isAutoSendEnabled),
    };
  } catch {
    return { language: 'vi-VN', isAutoSendEnabled: false };
  }
};

// Silence timeout in ms (2 seconds)
const SILENCE_TIMEOUT = 2000;

export const VoiceInput = ({
  onTranscriptChange,
  onFinalTranscript,
  onAutoSend,
  disabled,
}: VoiceInputProps) => {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);

  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const transcriptRef = useRef('');
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Clear silence timer
  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  // Stop and send
  const stopAndSend = useCallback(async () => {
    clearSilenceTimer();
    recognitionRef.current?.stop();
    setListening(false);

    const { isAutoSendEnabled } = getVoiceSettings();
    if (isAutoSendEnabled && onAutoSend && transcriptRef.current.trim()) {
      await onAutoSend(transcriptRef.current.trim());
    }
    transcriptRef.current = '';
    onTranscriptChange?.('');
  }, [onAutoSend, onTranscriptChange, clearSilenceTimer]);

  // Reset silence timer (called on each speech)
  const resetSilenceTimer = useCallback(() => {
    clearSilenceTimer();
    silenceTimerRef.current = setTimeout(() => {
      stopAndSend();
    }, SILENCE_TIMEOUT);
  }, [clearSilenceTimer, stopAndSend]);

  // Start recognition
  const start = useCallback(() => {
    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition || disabled) return;

    const recognition = new SpeechRecognition();
    recognition.interimResults = true;
    recognition.continuous = true; // Keep listening
    recognition.lang = getVoiceSettings().language;

    recognition.onresult = (event) => {
      let interim = '';
      let finalText = '';

      // Build full transcript from all results
      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result) continue;
        const text = result[0]?.transcript || '';
        if (result.isFinal) {
          finalText += text;
        } else {
          interim += text;
        }
      }

      // Show realtime (accumulated final + current interim)
      const display = transcriptRef.current
        ? `${transcriptRef.current} ${interim}`
        : interim || finalText;
      onTranscriptChange?.(display);

      if (finalText && !transcriptRef.current.includes(finalText.trim())) {
        transcriptRef.current = transcriptRef.current
          ? `${transcriptRef.current} ${finalText.trim()}`
          : finalText.trim();
        onFinalTranscript?.(finalText.trim());
      }

      // Reset silence timer on any speech activity
      resetSilenceTimer();
    };

    recognition.onerror = (e) => {
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.warn('Speech recognition error:', e.error);
      }
      clearSilenceTimer();
      setListening(false);
    };

    recognition.onend = () => {
      // Only set listening false if not manually stopped
      setListening(false);
    };

    recognitionRef.current = recognition;

    try {
      recognition.start();
      setListening(true);
      transcriptRef.current = '';
      // Start initial silence timer
      resetSilenceTimer();
    } catch (err) {
      console.error('Failed to start recognition:', err);
      setListening(false);
    }
  }, [disabled, onTranscriptChange, onFinalTranscript, resetSilenceTimer, clearSilenceTimer]);

  // Stop recognition (manual)
  const stop = useCallback(() => {
    stopAndSend();
  }, [stopAndSend]);

  // Toggle
  const toggle = useCallback(() => {
    if (listening) {
      stop();
    } else {
      start();
    }
  }, [listening, start, stop]);

  // Check support on mount
  useEffect(() => {
    setSupported(Boolean(getSpeechRecognition()));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearSilenceTimer();
      recognitionRef.current?.abort();
    };
  }, [clearSilenceTimer]);

  if (!supported) {
    return null;
  }

  return (
    <div
      className={styles.voiceStatus}
      title={listening ? 'Đang ghi âm... Nhấn để dừng' : 'Nhấn để ghi âm'}
    >
      <button
        type="button"
        onClick={toggle}
        className={`${styles.voiceButton} ${listening ? styles.listening : ''}`}
        disabled={disabled}
        aria-pressed={listening}
      >
        {listening ? <StopCircle size={18} /> : <Mic size={18} />}
      </button>
      {listening && <div className={styles.pulse} aria-hidden />}
    </div>
  );
};
