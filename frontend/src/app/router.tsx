/**
 * React Router Configuration - LegalRAG
 *
 * Public Routes:
 * - / → Chat page (no auth required)
 *
 * Admin Routes:
 * - /admin/login → Admin login
 * - /admin → Admin dashboard (auth required - TODO)
 */

import { createBrowserRouter } from 'react-router-dom';
import { ROUTES } from '@/constants';
import { MainLayout, AdminLayout } from '@/layouts';
// import { ProtectedRoute } from '@/components/auth'; // TODO: Enable when auth service ready

// Lazy load pages
import { lazy } from 'react';

// Pages with default export (no conversion needed)
const ChatPage = lazy(() => import('@/pages/ChatPage'));
const AdminLoginPage = lazy(() => import('@/pages/AdminLoginPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

// Pages with named export (need conversion)
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))
);
const CollectionsPage = lazy(() =>
  import('@/pages/CollectionsPage').then((m) => ({ default: m.CollectionsPage }))
);
const CollectionDetailPage = lazy(() =>
  import('@/pages/CollectionDetailPage').then((m) => ({ default: m.CollectionDetailPage }))
);
const UploadDocumentPage = lazy(() =>
  import('@/pages/UploadDocumentPage').then((m) => ({ default: m.UploadDocumentPage }))
);
const DocumentsPage = lazy(() =>
  import('@/pages/DocumentsPage').then((m) => ({ default: m.DocumentsPage }))
);
const DocumentDetailPage = lazy(() =>
  import('@/pages/DocumentDetailPage').then((m) => ({ default: m.DocumentDetailPage }))
);
const AdminPage = lazy(() => import('@/pages/AdminPage').then((m) => ({ default: m.AdminPage })));

export const router = createBrowserRouter([
  // ============ PUBLIC ROUTES ============
  // Root: Chat page (no auth)
  {
    path: ROUTES.HOME,
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <ChatPage />,
      },
    ],
  },

  // ============ ADMIN ROUTES ============
  // Admin login (public)
  {
    path: '/admin/login',
    element: <AdminLoginPage />,
  },

  // Admin dashboard (TODO: protect with auth)
  {
    path: ROUTES.ADMIN,
    element: <AdminLayout />,
    // element: ( // TODO: Uncomment when auth service ready
    //   <ProtectedRoute requiredRole="admin">
    //     <AdminLayout />
    //   </ProtectedRoute>
    // ),
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'collections',
        element: <CollectionsPage />,
      },
      {
        path: 'collections/:id',
        element: <CollectionDetailPage />,
      },
      {
        path: 'collections/:id/upload',
        element: <UploadDocumentPage />,
      },
      {
        path: 'documents',
        element: <DocumentsPage />,
      },
      {
        path: 'documents/:id',
        element: <DocumentDetailPage />,
      },
      // TODO: Add more admin routes
      // { path: 'stats', element: <StatsPage /> },
      // { path: 'settings', element: <SettingsPage /> },

      // Legacy AdminPage (will be removed)
      {
        path: 'old',
        element: <AdminPage />,
      },
    ],
  },

  // ============ 404 NOT FOUND ============
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
