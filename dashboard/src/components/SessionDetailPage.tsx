import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, 
  AppBar, 
  Toolbar, 
  IconButton, 
  Typography, 
  Box, 
  Paper, 
  Alert, 
  CircularProgress,
  Skeleton
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { apiClient, handleAPIError } from '../services/api';
import type { DetailedSession } from '../types';
import SessionHeader from './SessionHeader';
import OriginalAlertCard from './OriginalAlertCard';
import FinalAnalysisCard from './FinalAnalysisCard';
import SimpleTimeline from './SimpleTimeline';

/**
 * SessionDetailPage component - Phase 3
 * Displays comprehensive session details including original alert data, timeline, and final analysis
 */
function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  
  // Session detail state
  const [session, setSession] = useState<DetailedSession | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch session detail data
  const fetchSessionDetail = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching session detail for ID:', id);
      
      const sessionData = await apiClient.getSessionDetail(id);
      setSession(sessionData);
      console.log('Session detail loaded:', sessionData);
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setError(errorMessage);
      console.error('Failed to fetch session detail:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load session data when component mounts or sessionId changes
  useEffect(() => {
    if (sessionId) {
      fetchSessionDetail(sessionId);
    } else {
      setError('Session ID not provided');
      setLoading(false);
    }
  }, [sessionId]);

  // Handle back navigation
  const handleBack = () => {
    navigate('/dashboard');
  };

  // Handle retry
  const handleRetry = () => {
    if (sessionId) {
      fetchSessionDetail(sessionId);
    }
  };

  return (
    <Container maxWidth={false} sx={{ px: 2 }}>
      {/* AppBar with back button and title */}
      <AppBar position="static" elevation={0} sx={{ borderRadius: 1 }}>
        <Toolbar>
          <IconButton 
            edge="start" 
            color="inherit" 
            onClick={handleBack}
            sx={{ mr: 2 }}
            aria-label="Back to dashboard"
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Session Details
          </Typography>
          {loading && (
            <CircularProgress size={20} sx={{ color: 'inherit' }} />
          )}
        </Toolbar>
      </AppBar>

      <Box sx={{ mt: 2 }}>
        {/* Loading state */}
        {loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Session header skeleton */}
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Skeleton variant="circular" width={40} height={40} />
                <Box sx={{ flex: 1 }}>
                  <Skeleton variant="text" width="60%" height={32} />
                  <Skeleton variant="text" width="40%" height={20} />
                </Box>
                <Skeleton variant="text" width={100} height={24} />
              </Box>
            </Paper>

            {/* Original alert card skeleton */}
            <Paper sx={{ p: 3 }}>
              <Skeleton variant="text" width="30%" height={28} sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', gap: 3 }}>
                <Box sx={{ flex: 1 }}>
                  <Skeleton variant="rectangular" height={200} />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Skeleton variant="rectangular" height={200} />
                </Box>
              </Box>
            </Paper>

            {/* Timeline skeleton */}
            <Paper sx={{ p: 3 }}>
              <Skeleton variant="text" width="25%" height={28} sx={{ mb: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {[1, 2, 3].map((i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Box sx={{ flex: 1 }}>
                      <Skeleton variant="text" width="70%" />
                      <Skeleton variant="text" width="40%" />
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Box>
        )}

        {/* Error state */}
        {error && !loading && (
          <Alert 
            severity="error" 
            sx={{ mb: 2 }}
            action={
              <IconButton
                color="inherit"
                size="small"
                onClick={handleRetry}
                aria-label="Retry"
              >
                <Typography variant="button">Retry</Typography>
              </IconButton>
            }
          >
            <Typography variant="body1" gutterBottom>
              Failed to load session details
            </Typography>
            <Typography variant="body2">
              {error}
            </Typography>
          </Alert>
        )}

        {/* Session detail content */}
        {session && !loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Session Header */}
            <SessionHeader session={session} />

            {/* Original Alert Data */}
            <OriginalAlertCard alertData={session.alert_data} />

            {/* Processing Timeline */}
            <SimpleTimeline timelineItems={session.chronological_timeline} />

            {/* Final AI Analysis */}
            <FinalAnalysisCard 
              analysis={session.final_analysis}
              sessionStatus={session.status}
              errorMessage={session.error_message}
            />
          </Box>
        )}

        {/* Empty state for missing session */}
        {!session && !loading && !error && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body1">
              Session not found or no longer available
            </Typography>
          </Alert>
        )}
      </Box>
    </Container>
  );
}

export default SessionDetailPage; 