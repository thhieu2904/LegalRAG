/**
 * ProtectedRoute - Guard admin routes
 * Requires valid JWT token in localStorage
 */

import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const token = localStorage.getItem('admin_token');
  const expiresAt = localStorage.getItem('admin_token_expires');

  // Check if token exists
  if (!token) {
    return <Navigate to="/admin/login" replace />;
  }

  // Check if token is expired
  if (expiresAt && Date.now() > parseInt(expiresAt)) {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_token_expires');
    return <Navigate to="/admin/login" replace />;
  }

  return <>{children}</>;
};
