/**
 * useTTS Hook
 * Manages Web Speech API for text-to-speech functionality
 * Uses configuration from localStorage (VoiceSettings)
 */

import { useEffect, useRef, useCallback, useState } from 'react';

export interface TTSConfig {
  ttsEnabled: boolean;
  ttsVoice: string;
  ttsSpeed: number;
  ttsVolume: number;
}

export interface TTSState {
  isPlaying: boolean;
  isPaused: boolean;
  currentText: string;
  utteranceId: string | null;
}

export interface UseTTSReturn {
  state: TTSState;
  speak: (text: string, utteranceId?: string, forceSpeak?: boolean) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
  setConfig: (config: TTSConfig) => void;
  getAvailableVoices: () => SpeechSynthesisVoice[];
  isEnabled: () => boolean;
}

const DEFAULT_CONFIG: TTSConfig = {
  ttsEnabled: false,
  ttsVoice: '',
  ttsSpeed: 1.0,
  ttsVolume: 1.0,
};

export const useTTS = (): UseTTSReturn => {
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const configRef = useRef<TTSConfig>(DEFAULT_CONFIG);
  const [state, setState] = useState<TTSState>({
    isPlaying: false,
    isPaused: false,
    currentText: '',
    utteranceId: null,
  });

  // Load config from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('voiceSettings');
    if (stored) {
      try {
        const settings = JSON.parse(stored);
        configRef.current = {
          ttsEnabled: settings.ttsEnabled ?? DEFAULT_CONFIG.ttsEnabled,
          ttsVoice: settings.ttsVoice ?? DEFAULT_CONFIG.ttsVoice,
          ttsSpeed: settings.ttsSpeed ?? DEFAULT_CONFIG.ttsSpeed,
          ttsVolume: settings.ttsVolume ?? DEFAULT_CONFIG.ttsVolume,
        };
      } catch (error) {
        console.error('Failed to load TTS config from localStorage:', error);
      }
    }
  }, []);

  // Listen to localStorage changes (when VoiceSettings updates)
  useEffect(() => {
    const handleStorageChange = () => {
      const stored = localStorage.getItem('voiceSettings');
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          configRef.current = {
            ttsEnabled: settings.ttsEnabled ?? DEFAULT_CONFIG.ttsEnabled,
            ttsVoice: settings.ttsVoice ?? DEFAULT_CONFIG.ttsVoice,
            ttsSpeed: settings.ttsSpeed ?? DEFAULT_CONFIG.ttsSpeed,
            ttsVolume: settings.ttsVolume ?? DEFAULT_CONFIG.ttsVolume,
          };
        } catch (error) {
          console.error('Failed to parse TTS config:', error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const getAvailableVoices = useCallback((): SpeechSynthesisVoice[] => {
    return window.speechSynthesis.getVoices();
  }, []);

  const setConfig = useCallback((config: TTSConfig) => {
    configRef.current = config;
  }, []);

  const speak = useCallback(
    (text: string, utteranceId?: string, forceSpeak = false) => {
      // Reload config from localStorage BEFORE checking (fix bug: stale config)
      const stored = localStorage.getItem('voiceSettings');
      if (stored) {
        try {
          const settings = JSON.parse(stored);
          configRef.current = {
            ttsEnabled: settings.ttsEnabled ?? DEFAULT_CONFIG.ttsEnabled,
            ttsVoice: settings.ttsVoice ?? DEFAULT_CONFIG.ttsVoice,
            ttsSpeed: settings.ttsSpeed ?? DEFAULT_CONFIG.ttsSpeed,
            ttsVolume: settings.ttsVolume ?? DEFAULT_CONFIG.ttsVolume,
          };
        } catch (error) {
          console.error('Failed to reload TTS config:', error);
        }
      }

      // Check if TTS is enabled (unless forceSpeak for testing)
      if (!forceSpeak && !configRef.current.ttsEnabled) {
        console.warn('TTS is disabled');
        return;
      }

      // Stop any ongoing speech
      window.speechSynthesis.cancel();

      // Filter and clean text
      const cleanText = text
        .trim()
        .replace(/<[^>]*>/g, '') // Remove HTML tags
        .replace(/\n/g, ' ') // Replace newlines with space
        .replace(/\s+/g, ' '); // Replace multiple spaces with single space

      if (!cleanText) {
        console.warn('Text is empty after cleaning');
        return;
      }

      // Create utterance
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utteranceRef.current = utterance;

      // Get voice
      const voices = getAvailableVoices();
      if (configRef.current.ttsVoice && voices.length > 0) {
        const selectedVoice = voices.find((v) => v.name === configRef.current.ttsVoice);
        if (selectedVoice) {
          utterance.voice = selectedVoice;
        }
      }

      // Apply settings
      utterance.rate = configRef.current.ttsSpeed;
      utterance.volume = configRef.current.ttsVolume;
      utterance.pitch = 1.0;
      utterance.lang = 'vi-VN'; // Default to Vietnamese

      // Setup event listeners
      utterance.onstart = () => {
        setState((prev) => ({
          ...prev,
          isPlaying: true,
          isPaused: false,
          currentText: cleanText,
          utteranceId: utteranceId || null,
        }));
      };

      utterance.onend = () => {
        setState((prev) => ({
          ...prev,
          isPlaying: false,
          isPaused: false,
        }));
      };

      utterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
        setState((prev) => ({
          ...prev,
          isPlaying: false,
          isPaused: false,
        }));
      };

      utterance.onpause = () => {
        setState((prev) => ({
          ...prev,
          isPaused: true,
        }));
      };

      utterance.onresume = () => {
        setState((prev) => ({
          ...prev,
          isPaused: false,
        }));
      };

      // Start speech
      window.speechSynthesis.speak(utterance);
    },
    [getAvailableVoices]
  );

  const pause = useCallback(() => {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
    }
  }, []);

  const resume = useCallback(() => {
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  }, []);

  const stop = useCallback(() => {
    window.speechSynthesis.cancel();
    setState({
      isPlaying: false,
      isPaused: false,
      currentText: '',
      utteranceId: null,
    });
  }, []);

  const isEnabled = useCallback((): boolean => {
    const stored = localStorage.getItem('voiceSettings');
    if (stored) {
      try {
        const settings = JSON.parse(stored);
        return settings.ttsEnabled || false;
      } catch {
        return false;
      }
    }
    return false;
  }, []);

  return {
    state,
    speak,
    pause,
    resume,
    stop,
    setConfig,
    getAvailableVoices,
    isEnabled,
  };
};
