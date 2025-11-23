/**
 * ProtectedRoute Types
 */

export interface ProtectedRouteProps {
  children?: React.ReactNode;
  requiredRole?: 'giao_vien' | 'sinh_vien';
}
