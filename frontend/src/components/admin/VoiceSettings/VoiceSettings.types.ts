/**
 * VoiceSettings Component Types
 */

export interface VoiceSettingsProps {
  isOpen: boolean;
  onClose: () => void;
}

export interface VoiceSettingsState {
  // STT Settings
  isAutoSendEnabled: boolean;
  language: string;

  // TTS Settings (for future - reading responses)
  ttsEnabled: boolean;
  ttsVoice: string;
  ttsSpeed: number;
  ttsVolume: number;
}

export const DEFAULT_VOICE_SETTINGS: VoiceSettingsState = {
  isAutoSendEnabled: true, // Auto-send enabled by default
  language: 'vi-VN',
  ttsEnabled: true, // TTS enabled by default
  ttsVoice: '',
  ttsSpeed: 1.0,
  ttsVolume: 1.0,
};

export const LANGUAGE_OPTIONS = [
  { value: 'vi-VN', label: 'Tiếng Việt' },
  { value: 'en-US', label: 'English (US)' },
  { value: 'en-GB', label: 'English (UK)' },
];
