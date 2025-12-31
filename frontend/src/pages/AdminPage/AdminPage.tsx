/**
 * Admin Page - Dashboard (Placeholder)
 * TODO: Implement Collections & Documents Management UI
 */

import styles from './AdminPage.module.css';

export const AdminPage = () => {
  return (
    <div className={styles.adminPage}>
      <div className={styles.header}>
        <h1 className={styles.title}>Admin Dashboard</h1>
        <p className={styles.subtitle}>Quản lý Collections & Documents</p>
      </div>

      <div className={styles.content}>
        <div className={styles.placeholder}>
          <div className={styles.icon}>🚧</div>
          <h2>Đang xây dựng</h2>
          <p>Collections Management UI đang được phát triển...</p>
          <p className={styles.info}>Sử dụng API đã test để quản lý Collections và Documents</p>
        </div>
      </div>
    </div>
  );
};
