import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import DashboardLayout from './components/DashboardLayout';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy load components for better performance
const DashboardView = React.lazy(() => import('./components/DashboardView'));
const SessionDetailPage = React.lazy(() => import('./components/SessionDetailPage'));

function App() {
  return (
    <ErrorBoundary>
      <DashboardLayout>
        <Suspense fallback={
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        }>
          <Routes>
            <Route path="/dashboard" element={<DashboardView />} />
            <Route path="/" element={<DashboardView />} />
            <Route path="/sessions/:sessionId" element={<SessionDetailPage />} />
          </Routes>
        </Suspense>
      </DashboardLayout>
    </ErrorBoundary>
  );
}

export default App; 