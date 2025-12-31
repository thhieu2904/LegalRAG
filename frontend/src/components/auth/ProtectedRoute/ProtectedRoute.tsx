/**
 * ProtectedRoute Component
 * Guards routes and redirects based on authentication and role
 */

import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/stores';
import type { ProtectedRouteProps } from './ProtectedRoute.types';

export const ProtectedRoute = ({ children, requiredRole }: ProtectedRouteProps) => {
  const { user, isAuthenticated } = useAuthStore();

  // Not authenticated → redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Authenticated but wrong role → redirect to unauthorized
  if (requiredRole && user?.role?.code !== requiredRole) {
    console.warn(
      `Access denied: User role '${user?.role?.code}' does not match required role '${requiredRole}'`
    );
    return <Navigate to="/unauthorized" replace />;
  }

  // All checks passed → render children or outlet
  return children ? <>{children}</> : <Outlet />;
};
