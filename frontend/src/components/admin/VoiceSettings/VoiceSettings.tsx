/**
 * VoiceSettings Component
 * Admin sidebar for voice input/output settings
 */

import { useState, useEffect } from 'react';
import { X, Mic, Volume2, Info } from 'lucide-react';
import type { VoiceSettingsProps, VoiceSettingsState } from './VoiceSettings.types';
import { DEFAULT_VOICE_SETTINGS, LANGUAGE_OPTIONS } from './VoiceSettings.types';
import styles from './VoiceSettings.module.css';

export const VoiceSettings = ({ isOpen, onClose }: VoiceSettingsProps) => {
  const [settings, setSettings] = useState<VoiceSettingsState>(DEFAULT_VOICE_SETTINGS);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  // Load settings from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('voiceSettings');
    if (stored) {
      try {
        setSettings({ ...DEFAULT_VOICE_SETTINGS, ...JSON.parse(stored) });
      } catch (error) {
        console.error('Failed to load voice settings:', error);
      }
    }
  }, []);

  // Load available TTS voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = speechSynthesis.getVoices();
      setAvailableVoices(voices);

      // Auto-select first Vietnamese voice if none selected
      if (!settings.ttsVoice && voices.length > 0) {
        const viVoice = voices.find((v) => v.lang.startsWith('vi'));
        if (viVoice) {
          updateSetting('ttsVoice', viVoice.name);
        }
      }
    };

    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;

    return () => {
      speechSynthesis.onvoiceschanged = null;
    };
  }, [settings.ttsVoice]);

  // Save settings to localStorage
  const saveSettings = (newSettings: VoiceSettingsState) => {
    localStorage.setItem('voiceSettings', JSON.stringify(newSettings));
    setSettings(newSettings);
  };

  const updateSetting = <K extends keyof VoiceSettingsState>(
    key: K,
    value: VoiceSettingsState[K]
  ) => {
    const newSettings = { ...settings, [key]: value };
    saveSettings(newSettings);
  };

  const toggleAutoSend = () => {
    updateSetting('isAutoSendEnabled', !settings.isAutoSendEnabled);
  };

  const toggleTTS = () => {
    updateSetting('ttsEnabled', !settings.ttsEnabled);
  };

  // Calculate slider percentage for CSS custom property
  const getSliderPercent = (value: number, min: number, max: number) => {
    return ((value - min) / (max - min)) * 100;
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className={styles.overlay} onClick={onClose} />

      {/* Sidebar */}
      <div className={styles.sidebar}>
        {/* Header */}
        <div className={styles.header}>
          <h2 className={styles.title}>Cài đặt giọng nói</h2>
          <button onClick={onClose} className={styles.closeButton} title="Đóng">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* Speech-to-Text Settings */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <Mic className={styles.sectionIcon} />
              Nhận dạng giọng nói (STT)
            </h3>
            <p className={styles.sectionDescription}>
              Cấu hình cho tính năng chuyển giọng nói thành văn bản
            </p>

            {/* Auto-send toggle */}
            <div className={styles.toggleGroup}>
              <div className={styles.toggleLabel}>
                <div className={styles.toggleTitle}>Tự động gửi</div>
                <div className={styles.toggleDescription}>Tự động gửi câu hỏi khi dừng nói</div>
              </div>
              <button
                onClick={toggleAutoSend}
                className={`${styles.toggle} ${settings.isAutoSendEnabled ? styles.active : ''}`}
                type="button"
              >
                <div className={styles.toggleThumb} />
              </button>
            </div>

            {/* Language selection */}
            <div className={styles.formGroup}>
              <label htmlFor="language" className={styles.label}>
                Ngôn ngữ nhận dạng
              </label>
              <select
                id="language"
                value={settings.language}
                onChange={(e) => updateSetting('language', e.target.value)}
                className={styles.select}
              >
                {LANGUAGE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className={styles.infoBadge}>
              <Info size={14} />
              <span>Sử dụng Web Speech API của trình duyệt</span>
            </div>
          </section>

          <div className={styles.divider} />

          {/* Text-to-Speech Settings */}
          <section className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <Volume2 className={styles.sectionIcon} />
              Đọc văn bản (TTS)
            </h3>
            <p className={styles.sectionDescription}>
              Cấu hình cho tính năng đọc phản hồi bằng giọng nói (sắp ra mắt)
            </p>

            {/* TTS Enable toggle */}
            <div className={styles.toggleGroup}>
              <div className={styles.toggleLabel}>
                <div className={styles.toggleTitle}>Bật đọc tự động</div>
                <div className={styles.toggleDescription}>Tự động đọc phản hồi từ hệ thống</div>
              </div>
              <button
                onClick={toggleTTS}
                className={`${styles.toggle} ${settings.ttsEnabled ? styles.active : ''}`}
                type="button"
              >
                <div className={styles.toggleThumb} />
              </button>
            </div>

            {/* Voice selection */}
            <div className={styles.formGroup}>
              <label htmlFor="ttsVoice" className={styles.label}>
                Giọng đọc
              </label>
              <select
                id="ttsVoice"
                value={settings.ttsVoice}
                onChange={(e) => updateSetting('ttsVoice', e.target.value)}
                className={styles.select}
                disabled={!settings.ttsEnabled}
              >
                <option value="">Mặc định</option>
                {availableVoices.map((voice) => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            </div>

            {/* Speed slider */}
            <div className={styles.sliderGroup}>
              <div className={styles.sliderLabel}>
                <span>Tốc độ đọc</span>
                <span className={styles.sliderValue}>{settings.ttsSpeed.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={settings.ttsSpeed}
                onChange={(e) => updateSetting('ttsSpeed', parseFloat(e.target.value))}
                className={styles.slider}
                style={
                  {
                    '--slider-percent': `${getSliderPercent(settings.ttsSpeed, 0.5, 2)}%`,
                  } as React.CSSProperties
                }
                disabled={!settings.ttsEnabled}
              />
            </div>

            {/* Volume slider */}
            <div className={styles.sliderGroup}>
              <div className={styles.sliderLabel}>
                <span>Âm lượng</span>
                <span className={styles.sliderValue}>{Math.round(settings.ttsVolume * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.ttsVolume}
                onChange={(e) => updateSetting('ttsVolume', parseFloat(e.target.value))}
                className={styles.slider}
                style={
                  {
                    '--slider-percent': `${getSliderPercent(settings.ttsVolume, 0, 1)}%`,
                  } as React.CSSProperties
                }
                disabled={!settings.ttsEnabled}
              />
            </div>

            <div className={styles.infoBadge}>
              <Info size={14} />
              <span>Sử dụng Web Speech Synthesis API</span>
            </div>
          </section>
        </div>
      </div>
    </>
  );
};
