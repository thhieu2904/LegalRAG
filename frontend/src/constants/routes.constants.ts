/**
 * Route Path Constants
 */

export const ROUTES = {
  HOME: '/',
  CHAT: '/chat',
  ADMIN: '/admin',
  NOT_FOUND: '*',
} as const;

export const ROUTE_LABELS = {
  [ROUTES.HOME]: 'Trang chủ',
  [ROUTES.CHAT]: 'Chat',
  [ROUTES.ADMIN]: 'Admin',
} as const;
