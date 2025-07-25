import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ hasError: true, error, errorInfo });
    // Optionally log error to external service
    // logErrorToService(error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Paper sx={{ p: 4, m: 4, textAlign: 'center' }}>
          <Typography variant="h2" color="error" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" gutterBottom>
            {this.state.error?.message || 'An unexpected error occurred.'}
          </Typography>
          <Button variant="contained" color="primary" onClick={this.handleReload} sx={{ mt: 2 }}>
            Reload Page
          </Button>
          {this.state.errorInfo && (
            <Box sx={{ mt: 2, textAlign: 'left', maxWidth: 600, mx: 'auto', fontFamily: 'monospace', fontSize: '0.9rem', color: 'grey.700', background: '#f5f5f5', p: 2, borderRadius: 1 }}>
              <pre>{this.state.errorInfo.componentStack}</pre>
            </Box>
          )}
        </Paper>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary; 