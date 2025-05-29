import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx'; // .tsxに変更
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import './index.css';
import { AuthProvider } from 'react-oidc-context';
import { onSigninCallback, userManager } from './config';

const theme = createTheme();

// TypeScriptでは、getElementByIdの返り値がHTMLElement | nullなので、
// nullでないことを明示するか、nullチェックが必要です。
// ここでは `!` (Non-null assertion operator) を使ってnullでないことを示しています。
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider userManager={userManager} onSigninCallback={onSigninCallback}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <App />
        </ThemeProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
);