/**
 * Admin Login Page - Temporary simple login
 * TODO: Replace with real auth service integration
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './styles.module.css';

// Temporary hardcoded credentials
const TEMP_ADMIN_USERNAME = 'admin';
const TEMP_ADMIN_PASSWORD = 'admin123';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Temporary hardcoded check
    if (username === TEMP_ADMIN_USERNAME && password === TEMP_ADMIN_PASSWORD) {
      // Store simple auth state
      localStorage.setItem('isAdminLoggedIn', 'true');
      localStorage.setItem('adminUser', username);

      // Redirect to admin dashboard
      navigate('/admin');
    } else {
      setError('Sai tên đăng nhập hoặc mật khẩu');
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        <div className={styles.header}>
          <h1 className={styles.title}>LegalRAG Admin</h1>
          <p className={styles.subtitle}>Đăng nhập vào hệ thống quản trị</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.label}>
              Tên đăng nhập
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={styles.input}
              placeholder="admin"
              required
              autoFocus
            />
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Mật khẩu
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              placeholder="••••••••"
              required
            />
          </div>

          {error && <div className={styles.error}>{error}</div>}

          <button type="submit" className={styles.submitButton} disabled={loading}>
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>

        <div className={styles.footer}>
          <p className={styles.note}>
            <strong>Tạm thời:</strong> Dùng <code>admin</code> / <code>admin123</code>
          </p>
          <p className={styles.backLink}>
            <a href="/">← Quay lại trang chủ</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
