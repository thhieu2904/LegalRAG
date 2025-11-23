/**
 * TypingIndicator Component
 */

import { Bot } from 'lucide-react';
import styles from './TypingIndicator.module.css';

export const TypingIndicator = () => {
  return (
    <div className={styles.typingIndicator}>
      <div className={styles.avatar}>
        <Bot size={20} />
      </div>
      <div className={styles.content}>
        <span className={styles.text}>AI đang trả lời</span>
        <div className={styles.dots}>
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
};
