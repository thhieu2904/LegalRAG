/**
 * AdminLayout Component
 * Layout for Admin Dashboard with Sidebar Navigation
 */

import { Outlet } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Footer } from '@/components/layout/Footer';
import { Sidebar } from '@/components/layout/Sidebar';
import { useUIStore } from '@/stores/uiStore';
import styles from './AdminLayout.module.css';

export const AdminLayout = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  // Token validation is handled by ProtectedRoute
  // No need for additional check here

  return (
    <div className={styles.adminLayout}>
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={toggleSidebar} />

      {/* Main Content Area */}
      <div className={styles.contentWrapper}>
        {/* Header with Organization Branding */}
        <Header variant="admin" />

        {/* Page Content */}
        <main className={styles.content}>
          <Outlet />
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </div>
  );
};
