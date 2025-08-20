export interface TextToSpeechConfig {
  rate?: number; // Tốc độ đọc (0.1 - 10)
  pitch?: number; // Cao độ giọng (0 - 2)
  volume?: number; // Âm lượng (0 - 1)
  lang?: string; // Ngôn ngữ
  voiceIndex?: number; // Chỉ số giọng nói
}

export interface SpeechStatus {
  isPlaying: boolean;
  isPaused: boolean;
  isSupported: boolean;
  currentText?: string;
}

export class TextToSpeechService {
  private synthesis: SpeechSynthesis;
  private currentUtterance: SpeechSynthesisUtterance | null = null;
  private voices: SpeechSynthesisVoice[] = [];
  private config: Required<TextToSpeechConfig>;
  private statusCallbacks: ((status: SpeechStatus) => void)[] = [];
  private userHasInteracted: boolean = false;

  constructor(config: TextToSpeechConfig = {}) {
    this.synthesis = window.speechSynthesis;
    this.config = {
      rate: config.rate ?? 1.0,
      pitch: config.pitch ?? 1.0,
      volume: config.volume ?? 0.8,
      lang: config.lang ?? "vi-VN",
      voiceIndex: config.voiceIndex ?? -1,
    };

    // Lắng nghe khi danh sách giọng nói được tải
    this.loadVoices();
    if (this.isSupported()) {
      this.synthesis.addEventListener(
        "voiceschanged",
        this.loadVoices.bind(this)
      );
    }

    // Track user interaction for autoplay policy
    this.initUserInteractionTracking();
  }

  private initUserInteractionTracking(): void {
    const markUserInteracted = () => {
      this.userHasInteracted = true;
    };

    // Listen for various user interaction events
    const events = ["click", "keydown", "touchstart"];
    events.forEach((event) => {
      document.addEventListener(event, markUserInteracted, { once: true });
    });
  }

  private hasUserInteracted(): boolean {
    return this.userHasInteracted;
  }

  private loadVoices(): void {
    this.voices = this.synthesis.getVoices();
  }

  public isSupported(): boolean {
    return "speechSynthesis" in window;
  }

  public getVoices(): SpeechSynthesisVoice[] {
    return this.voices;
  }

  public getVietnameseVoices(): SpeechSynthesisVoice[] {
    return this.voices.filter(
      (voice) => voice.lang.startsWith("vi") || voice.lang.startsWith("en") // Fallback to English voices
    );
  }

  public speak(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.isSupported()) {
        reject(new Error("Trình duyệt không hỗ trợ Text-to-Speech"));
        return;
      }

      // Check if user has interacted with the page
      if (!this.hasUserInteracted()) {
        reject(
          new Error("Cần tương tác với trang trước khi sử dụng Text-to-Speech")
        );
        return;
      }

      // Dừng speech hiện tại nếu có
      this.stop();

      // Tạo utterance mới
      this.currentUtterance = new SpeechSynthesisUtterance(text);

      // Cấu hình utterance
      this.currentUtterance.rate = this.config.rate;
      this.currentUtterance.pitch = this.config.pitch;
      this.currentUtterance.volume = this.config.volume;
      this.currentUtterance.lang = this.config.lang;

      // Chọn giọng nói
      const selectedVoice = this.getSelectedVoice();
      if (selectedVoice) {
        this.currentUtterance.voice = selectedVoice;
      }

      // Event listeners
      this.currentUtterance.onstart = () => {
        this.notifyStatusChange({
          isPlaying: true,
          isPaused: false,
          isSupported: true,
          currentText: text,
        });
      };

      this.currentUtterance.onend = () => {
        this.notifyStatusChange({
          isPlaying: false,
          isPaused: false,
          isSupported: true,
          currentText: undefined,
        });
        resolve();
      };

      this.currentUtterance.onerror = (error) => {
        this.notifyStatusChange({
          isPlaying: false,
          isPaused: false,
          isSupported: true,
          currentText: undefined,
        });

        // Handle interrupted error gracefully (common when user clicks fast)
        if (error.error === "interrupted") {
          console.log("TTS interrupted (normal when user clicks fast)");
          resolve(); // Don't reject for interruptions
        } else {
          reject(new Error(`Lỗi Text-to-Speech: ${error.error}`));
        }
      };

      this.currentUtterance.onpause = () => {
        this.notifyStatusChange({
          isPlaying: true,
          isPaused: true,
          isSupported: true,
          currentText: text,
        });
      };

      this.currentUtterance.onresume = () => {
        this.notifyStatusChange({
          isPlaying: true,
          isPaused: false,
          isSupported: true,
          currentText: text,
        });
      };

      // Bắt đầu speech
      this.synthesis.speak(this.currentUtterance);
    });
  }

  public pause(): void {
    if (this.synthesis.speaking && !this.synthesis.paused) {
      this.synthesis.pause();
    }
  }

  public resume(): void {
    if (this.synthesis.paused) {
      this.synthesis.resume();
    }
  }

  public stop(): void {
    this.synthesis.cancel();
    this.currentUtterance = null;
    this.notifyStatusChange({
      isPlaying: false,
      isPaused: false,
      isSupported: true,
      currentText: undefined,
    });
  }

  public getStatus(): SpeechStatus {
    return {
      isPlaying: this.synthesis.speaking,
      isPaused: this.synthesis.paused,
      isSupported: this.isSupported(),
      currentText: this.currentUtterance?.text,
    };
  }

  public updateConfig(newConfig: Partial<TextToSpeechConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  private getSelectedVoice(): SpeechSynthesisVoice | null {
    // Nếu có chỉ định voice index cụ thể
    if (this.config.voiceIndex >= 0 && this.voices[this.config.voiceIndex]) {
      return this.voices[this.config.voiceIndex];
    }

    // Tìm giọng tiếng Việt
    const vietnameseVoices = this.getVietnameseVoices();
    if (vietnameseVoices.length > 0) {
      // Ưu tiên giọng tiếng Việt
      const viVoice = vietnameseVoices.find((voice) =>
        voice.lang.startsWith("vi")
      );
      if (viVoice) return viVoice;

      // Fallback to first available voice
      return vietnameseVoices[0];
    }

    return null;
  }

  public onStatusChange(callback: (status: SpeechStatus) => void): () => void {
    this.statusCallbacks.push(callback);

    // Return unsubscribe function
    return () => {
      const index = this.statusCallbacks.indexOf(callback);
      if (index > -1) {
        this.statusCallbacks.splice(index, 1);
      }
    };
  }

  private notifyStatusChange(status: SpeechStatus): void {
    this.statusCallbacks.forEach((callback) => callback(status));
  }

  // Utility method để clean text trước khi đọc
  public cleanTextForSpeech(text: string): string {
    return text
      .replace(/\n+/g, ". ") // Thay newline bằng dấu chấm
      .replace(/\s+/g, " ") // Normalize whitespace
      .replace(/[^\w\s\u00C0-\u024F\u1E00-\u1EFF.,!?;:()""''"-]/g, "") // Giữ lại ký tự cần thiết
      .trim();
  }
}

// Export singleton instance
export const textToSpeechService = new TextToSpeechService();
