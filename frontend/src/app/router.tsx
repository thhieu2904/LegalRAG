/**
 * React Router Configuration - LegalRAG
 *
 * Public Routes:
 * - / → Common document bookmarks
 * - /hanh-chinh-cong → Public services demo
 * - /chat → Existing AI chat
 * - /kiem-tra-ho-so → Dossier lookup demo
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
const loadingFallback = (
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
const BookmarksPage = lazy(() => import('@/pages/PublicPortal/BookmarksPage'));
const PublicServicesPage = lazy(() => import('@/pages/PublicPortal/PublicServicesPage'));
const DossierLookupPage = lazy(() => import('@/pages/PublicPortal/DossierLookupPage'));
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
  // Public workspace with four navigation tabs (no auth)
  {
    path: ROUTES.HOME,
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={loadingFallback}>
            <BookmarksPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.PUBLIC_SERVICES,
        element: (
          <Suspense fallback={loadingFallback}>
            <PublicServicesPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.CHAT,
        element: (
          <Suspense fallback={loadingFallback}>
            <ChatPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.DOSSIER_LOOKUP,
        element: (
          <Suspense fallback={loadingFallback}>
            <DossierLookupPage />
          </Suspense>
        ),
      },
      // Form Fill Page - nested under MainLayout
      {
        path: 'forms/:docId/:formFilename',
        element: (
          <Suspense fallback={loadingFallback}>
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
      <Suspense fallback={loadingFallback}>
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
          <Suspense fallback={loadingFallback}>
            <DashboardPage />
          </Suspense>
        ),
      },
      {
        path: 'collections',
        element: (
          <Suspense fallback={loadingFallback}>
            <CollectionsPage />
          </Suspense>
        ),
      },
      {
        path: 'collections/:id',
        element: (
          <Suspense fallback={loadingFallback}>
            <CollectionDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'collections/:id/upload',
        element: (
          <Suspense fallback={loadingFallback}>
            <UploadDocumentPage />
          </Suspense>
        ),
      },
      {
        path: 'documents',
        element: (
          <Suspense fallback={loadingFallback}>
            <DocumentsPage />
          </Suspense>
        ),
      },
      {
        path: 'documents/:id',
        element: (
          <Suspense fallback={loadingFallback}>
            <DocumentDetailPage />
          </Suspense>
        ),
      },
      {
        path: 'user-forms',
        element: (
          <Suspense fallback={loadingFallback}>
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
          <Suspense fallback={loadingFallback}>
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
      <Suspense fallback={loadingFallback}>
        <NotFoundPage />
      </Suspense>
    ),
  },
]);
