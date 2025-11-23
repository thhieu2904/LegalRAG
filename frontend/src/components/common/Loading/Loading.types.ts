/**
 * Loading Component Types
 */

export type LoadingType = 'spinner' | 'dots' | 'pulse';
export type LoadingSize = 'sm' | 'md' | 'lg';

export interface LoadingProps {
  type?: LoadingType;
  size?: LoadingSize;
  text?: string;
  fullScreen?: boolean;
  className?: string;
}
