/**
 * VoiceInput Component
 * Speech-to-text input using Web Speech API
 */

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff } from 'lucide-react';
import type {
  VoiceInputProps,
  RecordingState,
  SpeechRecognition,
  SpeechRecognitionEvent,
  VoiceSettings,
} from './VoiceInput.types';
import styles from './VoiceInput.module.css';

const DEFAULT_SETTINGS: VoiceSettings = {
  isAutoSendEnabled: false,
  language: 'vi-VN',
};

export const VoiceInput = ({
  onTranscriptChange,
  onFinalTranscript,
  onAutoSend,
  disabled = false,
  className = '',
}: VoiceInputProps) => {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle');
  const [isSupported, setIsSupported] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const silenceTimeoutRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);

  // Get voice settings from localStorage
  const getSettings = (): VoiceSettings => {
    try {
      const stored = localStorage.getItem('voiceSettings');
      return stored ? { ...DEFAULT_SETTINGS, ...JSON.parse(stored) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  };

  // Check browser support
  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) {
      setIsSupported(false);
      setError('Trình duyệt không hỗ trợ nhận dạng giọng nói');
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (silenceTimeoutRef.current) {
        clearTimeout(silenceTimeoutRef.current);
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Setup audio analyzer for voice detection
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
        if (analyserRef.current && recordingState !== 'idle') {
          analyserRef.current.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / bufferLength;

          // Detect speech (threshold: 20)
          setRecordingState(average > 20 ? 'speaking' : 'listening');
          animationRef.current = requestAnimationFrame(checkAudioLevel);
        }
      };

      checkAudioLevel();
    } catch (err) {
      console.warn('Cannot access microphone for audio analysis:', err);
      // Continue with speech recognition without visual feedback
    }
  };

  const startRecording = async () => {
    if (!isSupported || disabled) return;

    try {
      setError(null);

      const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognitionAPI();

      const settings = getSettings();

      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = settings.language;
      recognitionRef.current.maxAlternatives = 1;

      recognitionRef.current.onstart = () => {
        setRecordingState('listening');
        setupAudioAnalyzer();
      };

      recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';

        // Get results from current session only
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcript = result[0].transcript;

          if (result.isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        // Send interim transcript for live preview
        if (interimTranscript) {
          onTranscriptChange(interimTranscript);
        }

        // Handle final transcript
        if (finalTranscript) {
          onFinalTranscript(finalTranscript);

          // Auto-send if enabled
          const settings = getSettings();
          if (settings.isAutoSendEnabled && onAutoSend) {
            onAutoSend(finalTranscript);
          }
        }

        // Reset silence timeout (auto-stop after 2s of silence)
        if (silenceTimeoutRef.current) {
          clearTimeout(silenceTimeoutRef.current);
        }
        silenceTimeoutRef.current = window.setTimeout(() => {
          stopRecording();
        }, 2000);
      };

      recognitionRef.current.onerror = (event: Event & { error?: string }) => {
        const errorMsg = event.error;

        // Only show important errors, ignore common ones
        if (errorMsg && !['no-speech', 'aborted'].includes(errorMsg)) {
          setError(`Lỗi nhận dạng: ${errorMsg}`);
        }

        setRecordingState('idle');
      };

      recognitionRef.current.onend = () => {
        setRecordingState('idle');
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
      };

      recognitionRef.current.start();
    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Không thể bắt đầu ghi âm');
      setRecordingState('idle');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (silenceTimeoutRef.current) {
      clearTimeout(silenceTimeoutRef.current);
    }
    setRecordingState('idle');
  };

  const toggleRecording = () => {
    if (recordingState === 'idle') {
      startRecording();
    } else {
      stopRecording();
    }
  };

  // Get button class based on state
  const getButtonClass = () => {
    const classes = [styles.voiceButton];
    if (recordingState !== 'idle') {
      classes.push(styles[recordingState]);
    }
    if (className) {
      classes.push(className);
    }
    return classes.join(' ');
  };

  // Get icon class based on state
  const getIconClass = () => {
    return `${styles.icon} ${styles[disabled ? 'disabled' : recordingState]}`;
  };

  if (!isSupported) {
    return (
      <button
        type="button"
        disabled
        className={`${styles.voiceButton} ${className}`}
        title="Trình duyệt không hỗ trợ nhận dạng giọng nói"
      >
        <MicOff className={`${styles.icon} ${styles.disabled}`} />
      </button>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        disabled={disabled}
        onClick={toggleRecording}
        className={getButtonClass()}
        title={
          recordingState === 'idle'
            ? 'Nhấn để nói'
            : recordingState === 'listening'
              ? 'Đang lắng nghe...'
              : 'Đang ghi âm...'
        }
      >
        <Mic className={getIconClass()} />

        {/* Wave effect for listening/speaking states */}
        {recordingState !== 'idle' && (
          <div className={`${styles.waveEffect} ${styles[recordingState]}`} />
        )}

        {/* Status indicator */}
        {recordingState !== 'idle' && <div className={styles.statusDot} />}
      </button>

      {/* Error message */}
      {error && <div className={styles.errorMessage}>{error}</div>}
    </div>
  );
};
