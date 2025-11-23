/**
 * Not Found Page
 */

import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants';

export default function NotFoundPage() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        gap: '1rem',
      }}
    >
      <h1 style={{ fontSize: '4rem', margin: 0 }}>404</h1>
      <p style={{ fontSize: '1.5rem', margin: 0 }}>Trang không tồn tại</p>
      <Link
        to={ROUTES.CHAT}
        style={{
          marginTop: '1rem',
          padding: '0.75rem 1.5rem',
          backgroundColor: 'var(--primary-color)',
          color: 'white',
          borderRadius: '6px',
          textDecoration: 'none',
        }}
      >
        Về trang chủ
      </Link>
    </div>
  );
}
