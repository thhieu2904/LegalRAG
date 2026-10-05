/** Browser speech recognition only. Never creates a session on page load. */
export interface SpeechResult {
  isFinal: boolean;
  0: { transcript: string };
}

export interface Recognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: { results: ArrayLike<SpeechResult> }) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

export type RecognitionConstructor = new () => Recognition;

export function browserRecognition(): RecognitionConstructor | null {
  if (typeof window === 'undefined' || !window.isSecureContext) return null;
  const browser = window as Window & {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  };
  return browser.SpeechRecognition ?? browser.webkitSpeechRecognition ?? null;
}

export const speechErrorMessages: Record<string, string> = {
  network: 'Chưa nhận diện được lời nói lúc này. Hãy thử lại hoặc nhập bằng tay.',
  'not-allowed': 'Chưa được cấp quyền micro. Bạn có thể cấp quyền trong cài đặt trình duyệt.',
  'service-not-allowed': 'Trình duyệt không cho phép dịch vụ nhận diện giọng nói.',
  'audio-capture': 'Không tìm thấy micro hoặc micro đang không sử dụng được.',
  'no-speech': 'Chưa nhận được lời nói. Hãy bấm mic và nói lại.',
  'language-not-supported': 'Dịch vụ không hỗ trợ ngôn ngữ tiếng Việt.',
  aborted: 'Đã dừng nhận diện giọng nói.',
  'end-timeout': 'Chưa nhận được kết quả cuối. Hãy kiểm tra lại nội dung trong ô.',
};

export function createSpeechSession(
  Constructor: RecognitionConstructor,
  callbacks: { onText(text: string): void; onListening(value: boolean): void; onError(code: string): void },
  timers: Pick<typeof globalThis, 'setTimeout' | 'clearTimeout'> = globalThis,
) {
  const recognition = new Constructor();
  recognition.lang = 'vi-VN';
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;
  let disposed = false;
  let finished = false;
  let started = false;
  let sessionTimer: ReturnType<typeof setTimeout> | undefined;
  let stopTimer: ReturnType<typeof setTimeout> | undefined;

  const clearTimers = () => {
    if (sessionTimer !== undefined) timers.clearTimeout(sessionTimer);
    if (stopTimer !== undefined) timers.clearTimeout(stopTimer);
  };
  const finish = () => {
    if (finished || disposed) return;
    finished = true;
    clearTimers();
    callbacks.onListening(false);
  };
  const stop = () => {
    if (!started || disposed || finished || stopTimer !== undefined) return;
    try {
      recognition.stop();
      // Give Chrome time to deliver its final result after stop().
      stopTimer = timers.setTimeout(() => {
        if (finished || disposed) return;
        callbacks.onError('end-timeout');
        try { recognition.abort(); } catch { /* already ended */ }
        finish();
      }, 3000);
    } catch {
      finish();
    }
  };

  recognition.onresult = (event) => {
    if (disposed || finished) return;
    // Chrome returns a cumulative result list: replace the snapshot, do not
    // append all previous final results again. No transcript is logged.
    callbacks.onText(Array.from(event.results, (result) => result[0].transcript).join(' ').trim());
  };
  recognition.onerror = (event) => {
    if (disposed || finished) return;
    callbacks.onError(event.error);
    finish();
    try { recognition.abort(); } catch { /* already ended */ }
  };
  recognition.onend = finish;

  return {
    start() {
      if (disposed || started) return;
      started = true;
      callbacks.onListening(true);
      try {
        recognition.start();
        sessionTimer = timers.setTimeout(stop, 60000);
      } catch {
        callbacks.onError('not-allowed');
        finish();
      }
    },
    stop,
    dispose() {
      disposed = true;
      clearTimers();
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      if (started && !finished) {
        try { recognition.abort(); } catch { /* already ended */ }
      }
    },
  };
}
