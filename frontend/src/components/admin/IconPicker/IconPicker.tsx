/**
 * IconPicker Component
 * Grid select icon from lucide-react library
 */

import { useState, useMemo } from 'react';
import * as Icons from 'lucide-react';
import { Search } from 'lucide-react';
import type { IconPickerProps } from './IconPicker.types';
import styles from './IconPicker.module.css';

// Popular icons for legal/document management
const POPULAR_ICONS = [
  'FolderOpen',
  'Book',
  'FileText',
  'Briefcase',
  'Archive',
  'Package',
  'Layers',
  'Shield',
  'Scale',
  'Gavel',
  'Clipboard',
  'FileCheck',
  'FolderLock',
  'BookOpen',
  'Library',
  'Inbox',
  'FolderTree',
  'Files',
  'ScrollText',
  'FileStack',
] as const;

export const IconPicker = ({ selectedIcon, onSelectIcon, className = '' }: IconPickerProps) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter icons based on search
  const filteredIcons = useMemo(() => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return POPULAR_ICONS;

    return POPULAR_ICONS.filter((icon) => icon.toLowerCase().includes(query));
  }, [searchQuery]);

  const handleIconClick = (iconName: string) => {
    onSelectIcon(iconName);
  };

  return (
    <div className={`${styles.iconPicker} ${className}`}>
      {/* Search Input */}
      <div className={styles.searchBox}>
        <Search size={18} className={styles.searchIcon} />
        <input
          type="text"
          placeholder="Tìm kiếm icon..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={styles.searchInput}
        />
      </div>

      {/* Icon Grid */}
      <div className={styles.iconGrid}>
        {filteredIcons.length > 0 ? (
          filteredIcons.map((iconName) => {
            const iconMap = Icons as unknown as Record<string, typeof Icons.FolderOpen>;
            const IconComponent = iconMap[iconName] || Icons.FolderOpen;
            const isSelected = selectedIcon === iconName;

            return (
              <button
                key={iconName}
                type="button"
                onClick={() => handleIconClick(iconName)}
                className={`${styles.iconButton} ${isSelected ? styles.selected : ''}`}
                title={iconName}
              >
                <IconComponent size={24} />
              </button>
            );
          })
        ) : (
          <div className={styles.noResults}>
            <p>Không tìm thấy icon phù hợp</p>
          </div>
        )}
      </div>
    </div>
  );
};
