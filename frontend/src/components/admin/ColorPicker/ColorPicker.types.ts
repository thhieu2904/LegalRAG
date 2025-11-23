/**
 * ColorPicker Types
 */

export interface ColorOption {
  name: string;
  hex: string;
}

export interface ColorPickerProps {
  selectedColor: string;
  selectedIcon?: string; // Icon to preview with color
  onSelectColor: (color: string) => void;
  className?: string;
}
