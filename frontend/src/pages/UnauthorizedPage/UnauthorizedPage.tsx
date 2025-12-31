/**
 * Unauthorized Page Component
 * Displayed when user tries to access a route without proper role
 */

import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores';
import styles from './UnauthorizedPage.module.css';

export const UnauthorizedPage = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleGoHome = () => {
    const roleCode = user?.role?.code;

    if (roleCode === 'admin' || roleCode === 'giao_vien') {
      navigate('/admin');
    } else if (roleCode === 'sinh_vien') {
      navigate('/chat');
    } else {
      navigate('/login');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={styles.container}>
      <div className={styles.content}>
        <div className={styles.icon}>🚫</div>
        <h1 className={styles.title}>Truy cập bị từ chối</h1>
        <p className={styles.message}>
          Bạn không có quyền truy cập trang này.
          <br />
          Vui lòng kiểm tra lại vai trò của bạn.
        </p>

        {user && (
          <div className={styles.userInfo}>
            <p>
              <strong>Email:</strong> {user.email || 'N/A'}
            </p>
            <p>
              <strong>Vai trò:</strong> {user.role.name || user.role.code}
            </p>
          </div>
        )}

        <div className={styles.actions}>
          <button onClick={handleGoHome} className={styles.primaryButton}>
            ← Về trang chủ
          </button>
          <button onClick={handleLogout} className={styles.secondaryButton}>
            Đăng xuất
          </button>
        </div>
      </div>
    </div>
  );
};

export default UnauthorizedPage;
