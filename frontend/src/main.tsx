/**
 * LINE LIFF 便當訂購系統
 * 
 * 應用程式進入點
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { LiffProvider } from './contexts/LiffContext';
import App from './App';
import './i18n';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LiffProvider>
      <App />
    </LiffProvider>
  </StrictMode>,
);
