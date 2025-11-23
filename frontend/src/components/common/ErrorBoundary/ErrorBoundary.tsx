/**
 * ErrorBoundary Component
 */

import React, { Component } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import styles from './ErrorBoundary.module.css';
import type { ErrorBoundaryProps, ErrorBoundaryState } from './ErrorBoundary.types';

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to console
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className={styles.container}>
          <div className={styles.content}>
            <div className={styles.iconWrapper}>
              <AlertTriangle size={48} className={styles.icon} />
            </div>

            <h1 className={styles.title}>Có lỗi xảy ra</h1>

            <p className={styles.message}>
              Đã xảy ra lỗi không mong muốn. Vui lòng thử lại hoặc tải lại trang.
            </p>

            {import.meta.env.DEV && this.state.error && (
              <details className={styles.details}>
                <summary className={styles.detailsSummary}>Chi tiết lỗi (Development)</summary>
                <pre className={styles.errorStack}>{this.state.error.stack}</pre>
              </details>
            )}

            <div className={styles.actions}>
              <button className={styles.button} onClick={this.handleReset}>
                Thử lại
              </button>
              <button className={styles.buttonSecondary} onClick={this.handleReload}>
                <RefreshCw size={16} />
                Tải lại trang
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
