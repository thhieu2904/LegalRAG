/**
 * ColorPicker Component
 * Select color from predefined palette with icon preview
 */

import * as Icons from 'lucide-react';
import type { ColorPickerProps, ColorOption } from './ColorPicker.types';
import styles from './ColorPicker.module.css';

// Predefined color palette
const COLOR_PALETTE: ColorOption[] = [
  { name: 'Xanh dương', hex: '#3b82f6' }, // blue
  { name: 'Đỏ', hex: '#ef4444' }, // red
  { name: 'Xanh lá', hex: '#10b981' }, // green
  { name: 'Vàng', hex: '#f59e0b' }, // yellow
  { name: 'Tím', hex: '#8b5cf6' }, // purple
  { name: 'Hồng', hex: '#ec4899' }, // pink
  { name: 'Cam', hex: '#f97316' }, // orange
  { name: 'Xanh ngọc', hex: '#14b8a6' }, // teal
  { name: 'Xanh indigo', hex: '#6366f1' }, // indigo
  { name: 'Xanh cyan', hex: '#06b6d4' }, // cyan
  { name: 'Xanh lime', hex: '#84cc16' }, // lime
  { name: 'Xám', hex: '#6b7280' }, // gray
];

export const ColorPicker = ({
  selectedColor,
  selectedIcon = 'FolderOpen',
  onSelectColor,
  className = '',
}: ColorPickerProps) => {
  const handleColorClick = (hex: string) => {
    onSelectColor(hex);
  };

  // Get icon component for preview
  const iconMap = Icons as unknown as Record<string, typeof Icons.FolderOpen>;
  const IconComponent = iconMap[selectedIcon] || Icons.FolderOpen;

  return (
    <div className={`${styles.colorPicker} ${className}`}>
      {/* Preview */}
      <div className={styles.preview}>
        <div
          className={styles.previewIcon}
          style={{
            backgroundColor: `${selectedColor}15`, // 15 = ~8% opacity in hex
            color: selectedColor,
          }}
        >
          <IconComponent size={32} />
        </div>
        <div className={styles.previewInfo}>
          <span className={styles.previewLabel}>Màu đã chọn</span>
          <code className={styles.previewHex}>{selectedColor}</code>
        </div>
      </div>

      {/* Color Grid */}
      <div className={styles.colorGrid}>
        {COLOR_PALETTE.map((color) => {
          const isSelected = selectedColor.toLowerCase() === color.hex.toLowerCase();

          return (
            <button
              key={color.hex}
              type="button"
              onClick={() => handleColorClick(color.hex)}
              className={`${styles.colorButton} ${isSelected ? styles.selected : ''}`}
              title={color.name}
              style={{
                backgroundColor: color.hex,
              }}
            >
              {isSelected && <Icons.Check size={20} className={styles.checkIcon} strokeWidth={3} />}
            </button>
          );
        })}
      </div>
    </div>
  );
};
