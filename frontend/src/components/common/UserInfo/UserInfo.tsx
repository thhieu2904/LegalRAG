/**
 * UserInfo Component
 * Displays user name, role, and logout button in header
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import styles from './UserInfo.module.css';

export const UserInfo: React.FC = () => {
  const navigate = useNavigate();
  const { user, profile, fetchProfile, logout } = useAuthStore();

  // Fetch profile on component mount
  useEffect(() => {
    if (user && !profile) {
      fetchProfile();
    }
  }, [user, profile, fetchProfile]);

  // Handle logout
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!user) {
    return null;
  }

  // Get display name from profile or email
  const displayName = profile
    ? 'ten_giao_vien' in profile
      ? profile.ten_giao_vien
      : profile.ten_sinh_vien
    : user.email;

  // Get role badge class
  const getRoleBadgeClass = () => {
    switch (user.role.code) {
      case 'admin':
        return styles.roleAdmin;
      case 'giao_vien':
        return styles.roleAdmin; // Teacher uses admin style
      case 'sinh_vien':
        return styles.roleUser;
      default:
        return '';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.userDetails}>
        <p className={styles.userName}>{displayName}</p>
        <p className={`${styles.userRole} ${getRoleBadgeClass()}`}>
          {user.role.name || user.role.code}
        </p>
      </div>
      <button onClick={handleLogout} className={styles.logoutButton} aria-label="Đăng xuất">
        Đăng xuất
      </button>
    </div>
  );
};

export default UserInfo;
