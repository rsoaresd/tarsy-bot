import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from './App';

// EP-0004 Material-UI theme following design specifications
const theme = createTheme({
  palette: {
    primary: {
      main: '#2196F3', // Primary blue as specified
    },
    success: {
      main: '#4CAF50', // Success green
    },
    warning: {
      main: '#FF9800', // Warning orange  
    },
    error: {
      main: '#F44336', // Error red
    },
    info: {
      main: '#2196F3', // Info blue
    },
    background: {
      default: '#FAFAFA', // Light gray background
      paper: '#FFFFFF', // White content cards
    },
    text: {
      primary: '#333333', // Dark gray primary text
      secondary: '#666666', // Medium gray secondary text
    },
  },
  typography: {
    fontFamily: 'Roboto, Arial, sans-serif',
    h1: {
      fontSize: '24px',
      fontWeight: 500,
    },
    h2: {
      fontSize: '20px',
      fontWeight: 500,
    },
    h3: {
      fontSize: '18px',
      fontWeight: 500,
    },
    body1: {
      fontSize: '16px',
      fontWeight: 400,
    },
    body2: {
      fontSize: '14px',
      fontWeight: 400,
    },
    caption: {
      fontSize: '12px',
      fontWeight: 400,
    },
  },
  spacing: 8, // 8px base unit as specified
  shape: {
    borderRadius: 4,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          padding: '16px',
          margin: '16px 0',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          padding: '8px 12px',
          margin: '0 8px',
        },
      },
    },
  },
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
); 