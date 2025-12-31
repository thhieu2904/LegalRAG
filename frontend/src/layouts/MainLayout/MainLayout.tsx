/**
 * MainLayout Component
 * Layout for Chat Page (Public)
 */

import { Outlet } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import styles from './MainLayout.module.css';

export const MainLayout = () => {
  return (
    <div className={styles.mainLayout}>
      {/* Header */}
      <Header variant="chat" />

      {/* Main Content */}
      <main className={styles.content}>
        <Outlet />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
};
