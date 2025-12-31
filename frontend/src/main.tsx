import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '@/styles/globals.css';
import '@/styles/utilities.css';
import App from './App.tsx';
import { TTSProvider } from '@/hooks/useTTS';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <TTSProvider>
      <App />
    </TTSProvider>
  </StrictMode>
);
