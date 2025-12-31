/**
 * Loading Component
 */

import React from 'react';
import styles from './Loading.module.css';
import { cn } from '@/utils';
import type { LoadingProps } from './Loading.types';

export const Loading: React.FC<LoadingProps> = ({
  type = 'spinner',
  size = 'md',
  text,
  fullScreen = false,
  className,
}) => {
  const LoadingElement = () => {
    switch (type) {
      case 'spinner':
        return (
          <div className={cn(styles.spinner, styles[size])} role="status" aria-label="Loading">
            <div className={styles.spinnerCircle} />
          </div>
        );

      case 'dots':
        return (
          <div className={cn(styles.dots, styles[size])} role="status" aria-label="Loading">
            <div className={styles.dot} />
            <div className={styles.dot} />
            <div className={styles.dot} />
          </div>
        );

      case 'pulse':
        return (
          <div className={cn(styles.pulse, styles[size])} role="status" aria-label="Loading">
            <div className={styles.pulseCircle} />
          </div>
        );

      default:
        return null;
    }
  };

  const content = (
    <div className={cn(styles.container, className)}>
      <LoadingElement />
      {text && <p className={styles.text}>{text}</p>}
    </div>
  );

  if (fullScreen) {
    return <div className={styles.fullScreen}>{content}</div>;
  }

  return content;
};
