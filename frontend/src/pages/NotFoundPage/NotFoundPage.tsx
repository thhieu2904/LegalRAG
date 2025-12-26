/**
 * 404 Not Found Page
 */

import { Link } from 'react-router-dom';
import styles from './NotFoundPage.module.css';

export const NotFoundPage = () => {
  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <h1 className={styles.title}>404</h1>
        <p className={styles.message}>Không tìm thấy trang</p>
        <p className={styles.description}>Xin lỗi, trang bạn đang tìm kiếm không tồn tại.</p>
        <Link to="/" className={styles.homeLink}>
          Về trang chủ
        </Link>
      </div>
    </div>
  );
};

export default NotFoundPage;
