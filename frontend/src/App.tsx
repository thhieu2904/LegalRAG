/**
 * Root App Component
 */

import { Suspense } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';

function App() {
  return (
    <Suspense
      fallback={
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
      }
    >
      <RouterProvider router={router} />
    </Suspense>
  );
}

export default App;
