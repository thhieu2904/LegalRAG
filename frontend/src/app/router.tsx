/**
 * React Router Configuration - LegalRAG
 *
 * Public Routes:
 * - / → Chat page (no auth required)
 *
 * Admin Routes:
 * - /admin/login → Admin login
 * - /admin → Admin dashboard (JWT auth required)
 */

import { createBrowserRouter } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { ROUTES } from '@/constants';
import { MainLayout, AdminLayout } from '@/layouts';
import { ProtectedRoute } from '@/components/ProtectedRoute';

// Loading fallback component
const LoadingFallback = () => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      fontSize: '1.5rem',
    }}
  >
    Đang tải...
  </div>
);

// Lazy load pages
// Pages with default export (no conversion needed)
const ChatPage = lazy(() => import('@/pages/ChatPage'));
const AdminLoginPage = lazy(() =>
  import('@/pages/AdminLoginPage').then((m) => ({ default: m.AdminLoginPage }))
);
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
const FormFillPage = lazy(() =>
  import('@/pages/FormFillPage').then((m) => ({ default: m.FormFillPage }))
);
const UserFormsPage = lazy(() =>
  import('@/pages/UserFormsPage').then((m) => ({ default: m.UserFormsPage }))
);

export const router = createBrowserRouter([
  // ============ PUBLIC ROUTES ============
  // Root: Chat page (no auth)
  {
    path: ROUTES.HOME,
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <ChatPage />
          </Suspense>
        ),
      },
      // Form Fill Page - nested under MainLayout
      {
        path: 'forms/:docId/:formFilename',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <FormFillPage />
          </Suspense>
        ),
      },
    ],
  },

  // ============ ADMIN ROUTES ============
  // Admin login (public)
  {
    path: '/admin/login',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <AdminLoginPage />
      </Suspense>
    ),
  },

  // Admin dashboard (protected with JWT)
  {
    path: ROUTES.ADMIN,
    element: (
      <ProtectedRoute>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: 'collections',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <CollectionsPage />
          </Suspense>
        ),
      },
      {
        path: 'collections/:id',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <CollectionDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'collections/:id/upload',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <UploadDocumentPage />
          </Suspense>
        ),
      },
      {
        path: 'documents',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <DocumentsPage />
          </Suspense>
        ),
      },
      {
        path: 'documents/:id',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <DocumentDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'user-forms',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <UserFormsPage />
          </Suspense>
        ),
      },
      // TODO: Add more admin routes
      // { path: 'stats', element: <StatsPage /> },
      // { path: 'settings', element: <SettingsPage /> },

      // Legacy AdminPage (will be removed)
      {
        path: 'old',
        element: (
          <Suspense fallback={<LoadingFallback />}>
            <AdminPage />
          </Suspense>
        ),
      },
    ],
  },

  // ============ 404 NOT FOUND ============
  {
    path: '*',
    element: (
      <Suspense fallback={<LoadingFallback />}>
        <NotFoundPage />
      </Suspense>
    ),
  },
]);
