/**
 * TypingIndicator Component
 */

import styles from './TypingIndicator.module.css';

export const TypingIndicator = () => {
  return (
    <div className={styles.typingIndicator}>
      <div className={styles.avatar}>
        <img src="/LOGO_HCC.jpg" alt="AI Assistant" className={styles.botAvatar} />
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
