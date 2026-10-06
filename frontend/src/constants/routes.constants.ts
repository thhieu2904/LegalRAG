/**
 * Route Path Constants
 */

export const ROUTES = {
  HOME: '/',
  PUBLIC_SERVICES: '/hanh-chinh-cong',
  CHAT: '/chat',
  DOSSIER_LOOKUP: '/kiem-tra-ho-so',
  ADMIN: '/admin',
  NOT_FOUND: '*',
} as const;

export const ROUTE_LABELS = {
  [ROUTES.HOME]: 'Văn bản thường gặp',
  [ROUTES.PUBLIC_SERVICES]: 'Hành chính công',
  [ROUTES.CHAT]: 'Chat AI',
  [ROUTES.DOSSIER_LOOKUP]: 'Kiểm tra hồ sơ',
  [ROUTES.ADMIN]: 'Admin',
} as const;
