/**
 * IconPicker Types
 */

export interface IconPickerProps {
  selectedIcon: string;
  onSelectIcon: (icon: string) => void;
  className?: string;
}
