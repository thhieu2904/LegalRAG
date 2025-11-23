/**
 * Sidebar Component Types
 */

export interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export interface MenuItem {
  path: string;
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  exact?: boolean;
}
