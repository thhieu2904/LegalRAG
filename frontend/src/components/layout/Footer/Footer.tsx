/**
 * Footer Component - LegalRAG System
 */

import styles from './Footer.module.css';
import type { FooterProps } from './Footer.types';

export const Footer = ({ className }: FooterProps) => {
  return (
    <footer className={`${styles.footer} ${className || ''}`}>
      <div className={styles.container}>
        {/* Organization Info */}
        <div className={styles.organization}>
          <span className={styles.label}>Cơ quan chủ quản:</span> TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG
          XÃ LONG PHÚ
        </div>

        {/* Contact Info */}
        <div className={styles.contact}>
          <span className={styles.label}>Địa chỉ:</span> Ấp 4, xã Long Phú, TP Cần Thơ
          {' | '}
          <span className={styles.label}>Điện thoại:</span> 0907007397
        </div>
      </div>
    </footer>
  );
};
