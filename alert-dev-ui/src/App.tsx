/**
 * Main App component for the SRE AI Agent alert dev UI
 */

import React, { useState, useEffect } from 'react';
import {
  CssBaseline,
  ThemeProvider,
  createTheme,
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  Button,
  Alert,
  Fade,
} from '@mui/material';
import {
  Psychology as BrainIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { AlertResponse } from './types';
import AlertForm from './components/AlertForm';
import ProcessingStatus from './components/ProcessingStatus';
import ApiService from './services/api';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
});

type AppState = 'form' | 'processing' | 'completed';

function App() {
  const [appState, setAppState] = useState<AppState>('form');
  const [currentAlert, setCurrentAlert] = useState<AlertResponse | null>(null);
  const [backendStatus, setBackendStatus] = useState<'unknown' | 'healthy' | 'error'>('unknown');

  // Check backend health on app start
  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        await ApiService.healthCheck();
        setBackendStatus('healthy');
      } catch (error) {
        setBackendStatus('error');
        console.error('Backend health check failed:', error);
      }
    };

    checkBackendHealth();
  }, []);

  const handleAlertSubmitted = (alertResponse: AlertResponse) => {
    setCurrentAlert(alertResponse);
    setAppState('processing');
  };

  const handleProcessingComplete = () => {
    setAppState('completed');
  };

  const handleNewAlert = () => {
    setAppState('form');
    setCurrentAlert(null);
  };

  const renderContent = () => {
    switch (appState) {
      case 'form':
        return (
          <Fade in timeout={500}>
            <Box>
              <AlertForm onAlertSubmitted={handleAlertSubmitted} />
            </Box>
          </Fade>
        );

      case 'processing':
        return (
          <Fade in timeout={500}>
            <Box>
              {currentAlert && (
                <ProcessingStatus
                  alertId={currentAlert.alert_id}
                  onComplete={handleProcessingComplete}
                />
              )}
            </Box>
          </Fade>
        );

      case 'completed':
        return (
          <Fade in timeout={500}>
            <Box>
              {currentAlert && (
                <>
                  <ProcessingStatus
                    alertId={currentAlert.alert_id}
                    onComplete={handleProcessingComplete}
                  />
                  <Box mt={3} display="flex" justifyContent="center">
                    <Button
                      variant="outlined"
                      startIcon={<RefreshIcon />}
                      onClick={handleNewAlert}
                      size="large"
                    >
                      Analyze Another Alert
                    </Button>
                  </Box>
                </>
              )}
            </Box>
          </Fade>
        );

      default:
        return null;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <BrainIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SRE AI Agent
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            Automated Incident Response
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {/* Backend status indicator */}
        {backendStatus === 'error' && (
          <Alert severity="error" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Backend Unavailable:</strong> The SRE AI Agent backend is not responding. 
              Please ensure the backend server is running on port 8000.
            </Typography>
          </Alert>
        )}

        {backendStatus === 'healthy' && appState === 'form' && (
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2">
              🚀 SRE AI Agent is ready! Submit an alert to see automated incident analysis in action.
            </Typography>
          </Alert>
        )}

        {/* Main content */}
        <Box>
          {renderContent()}
        </Box>

        {/* Footer */}
        <Box mt={6} textAlign="center">
          <Typography variant="body2" color="text.secondary">
            SRE AI Agent v1.0 - Powered by AI and MCP Servers
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" mt={1}>
            Submit alerts to get automated runbook analysis and system diagnostics
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App; 