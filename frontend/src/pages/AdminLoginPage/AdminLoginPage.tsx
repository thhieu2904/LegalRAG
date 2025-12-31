/**
 * AdminLoginPage
 * Simple JWT authentication for admin panel
 * Internal use only - no complex OAuth needed
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, User, AlertCircle } from 'lucide-react';
import { apiClient } from '@/services/api/client';
import styles from './AdminLoginPage.module.css';

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export const AdminLoginPage = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', {
        username,
        password,
      });

      // Store token
      localStorage.setItem('admin_token', response.data.access_token);

      // Store expiry time
      const expiresAt = Date.now() + response.data.expires_in * 1000;
      localStorage.setItem('admin_token_expires', expiresAt.toString());

      // Redirect to admin dashboard
      navigate('/admin');
    } catch (err) {
      console.error('Login error:', err);
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        <div className={styles.header}>
          <Lock size={48} className={styles.icon} />
          <h1>Admin Login</h1>
          <p>LegalRAG System Administrator</p>
        </div>

        <form onSubmit={handleLogin} className={styles.form}>
          {error && (
            <div className={styles.error}>
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className={styles.inputGroup}>
            <label htmlFor="username">
              <User size={16} />
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
              autoFocus
              autoComplete="username"
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">
              <Lock size={16} />
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className={styles.submitButton} disabled={loading}>
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className={styles.footer}>
          <small>Internal use only - Authorized personnel only</small>
          <button type="button" className={styles.backButton} onClick={() => navigate('/')}>
            Back to Chat
          </button>
        </div>
      </div>
    </div>
  );
};
