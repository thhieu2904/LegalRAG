/**
 * Admin Dashboard - Overview Page
 * Displays system statistics and quick actions
 */

import styles from './DashboardPage.module.css';

export const DashboardPage = () => {
  return (
    <div className={styles.dashboard}>
      <h1 className={styles.title}>Tổng quan hệ thống</h1>

      <div className={styles.statsGrid}>
        {/* Placeholder stats cards */}
        <div className={styles.statCard}>
          <div className={styles.statIcon}>📁</div>
          <div className={styles.statValue}>0</div>
          <div className={styles.statLabel}>Bộ sưu tập</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>📄</div>
          <div className={styles.statValue}>0</div>
          <div className={styles.statLabel}>Tài liệu</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>✅</div>
          <div className={styles.statValue}>0</div>
          <div className={styles.statLabel}>Đã xử lý</div>
        </div>

        <div className={styles.statCard}>
          <div className={styles.statIcon}>⏳</div>
          <div className={styles.statValue}>0</div>
          <div className={styles.statLabel}>Đang xử lý</div>
        </div>
      </div>

      <div className={styles.placeholder}>
        <div className={styles.placeholderIcon}>🚧</div>
        <h2>Dashboard đang được phát triển</h2>
        <p>Chức năng thống kê và báo cáo sẽ được bổ sung trong các phiên bản tiếp theo.</p>
      </div>
    </div>
  );
};
