/**
 * Login Page Component
 * Handles user authentication for both giáo_viên and sinh_viên
 */

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores';
import styles from './LoginPage.module.css';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    clearError();

    try {
      const response = await login(username, password);

      // Router logic based on role code
      const roleCode = response.user.role.code;

      if (roleCode === 'admin') {
        navigate('/admin', { replace: true });
      } else if (roleCode === 'giao_vien') {
        navigate('/admin', { replace: true }); // Teacher → admin page
      } else if (roleCode === 'sinh_vien') {
        navigate('/chat', { replace: true }); // Student → chat page
      } else {
        navigate('/chat', { replace: true }); // Default
      }
    } catch (err) {
      // Error is handled by store
      console.error('Login failed:', err);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.loginBox}>
        <div className={styles.header}>
          <h1 className={styles.title}>🎓 AI Center</h1>
          <p className={styles.subtitle}>Hệ thống Hỏi đáp thông minh</p>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {error && (
            <div className={styles.errorAlert} role="alert">
              <span className={styles.errorIcon}>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <div className={styles.formGroup}>
            <label htmlFor="username" className={styles.label}>
              Tên đăng nhập
            </label>
            <input
              id="username"
              type="text"
              className={styles.input}
              placeholder="MSSV hoặc MSGV"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              disabled={isLoading}
            />
            <span className={styles.hint}>Ví dụ: SV001, GV001</span>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="password" className={styles.label}>
              Mật khẩu
            </label>
            <input
              id="password"
              type="password"
              className={styles.input}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading || !username || !password}
          >
            {isLoading ? (
              <>
                <span className={styles.spinner}></span>
                <span>Đang đăng nhập...</span>
              </>
            ) : (
              <>
                <span>Đăng nhập</span>
                <span className={styles.arrow}>→</span>
              </>
            )}
          </button>
        </form>

        <div className={styles.footer}>
          <p className={styles.footerText}>Dành cho giáo viên và sinh viên Đại học Trà Vinh</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
