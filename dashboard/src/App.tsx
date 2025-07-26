import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { theme } from './theme';
import DashboardView from './components/DashboardView';
import SessionDetailPage from './components/SessionDetailPage';

/**
 * Main App component for the Tarsy Dashboard - Phase 3
 * Provides React Router setup with dashboard and session detail routes
 */
function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          {/* Main dashboard route */}
          <Route path="/" element={<DashboardView />} />
          <Route path="/dashboard" element={<DashboardView />} />
          
          {/* Session detail route */}
          <Route path="/sessions/:sessionId" element={<SessionDetailPage />} />
          
          {/* Catch-all route redirects to dashboard */}
          <Route path="*" element={<DashboardView />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
