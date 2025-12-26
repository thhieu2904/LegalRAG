/**
 * Header Component - LegalRAG System
 * Consistent header for both Chat and Admin pages
 * Admin adds Sidebar + Menu button (mobile)
 */

import { Menu } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUIStore } from '@/stores/uiStore';
import styles from './Header.module.css';
import type { HeaderProps } from './Header.types';

export const Header = ({ variant = 'chat' }: HeaderProps) => {
  const { toggleSidebar } = useUIStore();

  return (
    <header className={styles.header}>
      <div className={styles.container}>
        {/* Mobile Menu Button (Admin only) */}
        {variant === 'admin' && (
          <button
            onClick={toggleSidebar}
            className={styles.mobileMenuButton}
            aria-label="Toggle sidebar"
            title="Menu"
          >
            <Menu size={24} />
          </button>
        )}

        {/* Logo Section (Left) */}
        <div className={styles.logoSection}>
          <img src="/LOGO_HCC.jpg" alt="Logo Trung tâm Hành chính công" className={styles.logo} />
        </div>

        {/* Title Section (Center) */}
        <div className={styles.titleSection}>
          <h1 className={styles.organizationName}>TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ</h1>
        </div>

        {/* Assistant Info Section (Right) */}
        <div className={styles.assistantSection}>
          <div className={styles.assistantInfo}>
            <div className={styles.assistantText}>
              <div className={styles.assistantName}>Trợ lý Pháp luật AI</div>
              <div className={styles.assistantDescription}>
                Hệ thống hỗ trợ thông tin thủ tục hành chính
              </div>
            </div>
            {/* Admin login removed - access via direct URL: /admin/login */}
            {variant !== 'chat' && (
              <Link to="/" className={styles.backButton} title="Trang chủ">
                Trang chủ
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
