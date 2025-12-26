/**
 * Sidebar Component
 * Navigation menu for Admin Dashboard
 */

import { LayoutDashboard, FolderOpen, LogOut, Mic2, FileCheck } from 'lucide-react';
import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { cn } from '@/utils/helpers/className';
import { VoiceSettings } from '@/components/admin/VoiceSettings';
import styles from './Sidebar.module.css';
import type { SidebarProps, MenuItem } from './Sidebar.types';

const menuItems: MenuItem[] = [
  { path: '/admin', icon: LayoutDashboard, label: 'Tổng quan', exact: true },
  { path: '/admin/collections', icon: FolderOpen, label: 'Bộ thủ tục' },
  { path: '/admin/user-forms', icon: FileCheck, label: 'Biểu mẫu đã điền' },
];

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const navigate = useNavigate();
  const [isVoiceSettingsOpen, setIsVoiceSettingsOpen] = useState(false);

  const handleLogout = () => {
    // Clear JWT token
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_token_expires');
    navigate('/admin/login', { replace: true });
  };

  return (
    <>
      {/* Overlay (Mobile only) */}
      {isOpen && <div className={styles.overlay} onClick={onClose} />}

      {/* Sidebar */}
      <aside className={cn(styles.sidebar, isOpen && styles.open)}>
        {/* Logo Section */}
        <div className={styles.logoSection}>
          <img src="/LOGO_HCC.jpg" alt="Logo" className={styles.logo} />
          <div className={styles.logoText}>
            <div className={styles.logoTitle}>Admin Panel</div>
            <div className={styles.logoSubtitle}>LegalRAG System</div>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className={styles.nav}>
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              className={({ isActive }) => cn(styles.navItem, isActive && styles.active)}
              onClick={onClose} // Close sidebar on mobile after click
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}

          {/* Voice Settings Menu Item */}
          <button
            className={styles.navItem}
            onClick={() => {
              setIsVoiceSettingsOpen(true);
              onClose(); // Close sidebar on mobile
            }}
          >
            <Mic2 size={20} />
            <span>Cài đặt giọng nói</span>
          </button>
        </nav>

        {/* Logout Button */}
        <div className={styles.footer}>
          <button className={styles.logoutBtn} onClick={handleLogout}>
            <LogOut size={20} />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Voice Settings Sidebar */}
      <VoiceSettings isOpen={isVoiceSettingsOpen} onClose={() => setIsVoiceSettingsOpen(false)} />
    </>
  );
};
