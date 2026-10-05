import { useEffect, useRef, useState } from 'react';
import { Mic, Square } from 'lucide-react';
import { browserRecognition, createSpeechSession, speechErrorMessages } from '../speech';
import styles from './EditablePlaceholder.module.css';

interface FieldDictationProps {
  value: string;
  onChange: (text: string) => void;
  onListeningChange: (listening: boolean) => void;
}

export function FieldDictation({ value, onChange, onListeningChange }: FieldDictationProps) {
  const [listening, setListening] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [error, setError] = useState('');
  const session = useRef<ReturnType<typeof createSpeechSession> | null>(null);
  const supported = Boolean(browserRecognition());

  useEffect(() => () => session.current?.dispose(), []);

  const start = () => {
    const Constructor = browserRecognition();
    if (!Constructor || listening) return;
    session.current?.dispose();
    setError('');
    session.current = createSpeechSession(Constructor, {
      onText: (text) => {
        if (text.trim()) onChange(text.slice(0, 2000));
      },
      onListening: (active) => {
        setListening(active);
        if (!active) setStopping(false);
        onListeningChange(active);
      },
      onError: (code) => setError(speechErrorMessages[code] ?? 'Không nhận diện được lời nói. Bạn vẫn có thể gõ.'),
    });
    session.current.start();
  };

  const stop = () => {
    setStopping(true);
    session.current?.stop();
  };

  return (
    <section className={styles.dictation} aria-label="Nhập bằng giọng nói">
      {!supported ? <p role="status">Chưa dùng được mic trên thiết bị này. Bạn vẫn có thể gõ.</p> : (
        <>
          <p>{listening ? 'Chữ đang hiện trong ô; bạn có thể sửa khi nói xong.' : value.trim() ? 'Bạn có thể sửa chữ trong ô. Nói lại sẽ thay nội dung hiện tại.' : 'Bấm để nói, chữ sẽ hiện ngay trong ô này.'}</p>
          <button
            type="button"
            className={`${styles.voiceButton} ${listening ? styles.voiceActive : ''}`}
            disabled={stopping}
            onClick={listening ? stop : start}
          >
            {listening ? <Square size={16} /> : <Mic size={16} />}
            {stopping ? 'Đang hoàn tất…' : listening ? 'Dừng' : value.trim() ? 'Nói lại' : 'Bấm để nói'}
          </button>
          <span className={styles.voiceStatus} role="status" aria-live="polite">
            {stopping ? 'Đang chờ kết quả cuối…' : listening ? 'Đang nghe…' : ''}
          </span>
          {error && <p className={styles.voiceError} role="alert">{error}</p>}
        </>
      )}
    </section>
  );
}
