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
import { webSocketService } from '../services/websocket';
import type { DetailedSession, SessionUpdate } from '../types';
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

  // Set up WebSocket event handlers for real-time updates
  useEffect(() => {
    if (!sessionId) return;

    // Handle session updates (status changes, progress updates, etc.)
    const handleSessionUpdate = (update: SessionUpdate) => {
      console.log('SessionDetailPage received session update:', update);
      
      // Only process updates for the current session
      if (update.session_id === sessionId) {
        console.log('Processing update for current session:', sessionId);
        
        // Check if this update contains timeline-related data - handle incrementally
        if (update.data && (update.data.interaction_type === 'llm' || update.data.interaction_type === 'mcp')) {
          console.log('Timeline interaction found in session update, updating timeline');
          // This case should be rare now that we use session-specific updates
          // But keeping minimal handling to avoid full refetch
          return;
        }
        
        // Check if this is a status change - handle incrementally
        if (update.data && update.data.type === 'session_status_change') {
          console.log('Session status change found in session update, updating status');
          // This is likely duplicate of session-specific handler, so just update status
          setSession(prevSession => {
            if (!prevSession) return prevSession;
            return {
              ...prevSession,
              status: update.data.status || prevSession.status,
              completed_at_us: update.data.status === 'completed' ? Date.now() * 1000 : prevSession.completed_at_us,
              final_analysis: update.data.final_analysis || prevSession.final_analysis,
              error_message: update.data.error_message || prevSession.error_message
            };
          });
          return;
        }
        
        // Update session with new data from the update
        setSession(prevSession => {
          if (!prevSession) return prevSession;
          
          const updatedSession = {
            ...prevSession,
            status: update.status,
            duration_ms: update.duration_ms ?? prevSession.duration_ms,
            error_message: update.error_message ?? prevSession.error_message,
            completed_at_us: update.completed_at_us ?? prevSession.completed_at_us
          };
          
          console.log('Updated session state:', updatedSession);
          return updatedSession;
        });
      } else {
        console.log('Ignoring update for different session:', update.session_id);
      }
    };

    // Handle session-specific timeline updates (LLM/MCP interactions)
    const handleSessionSpecificUpdate = (data: any) => {
      console.log('SessionDetailPage received session-specific update:', data);
      
      // Handle session status changes - update session state without refetching
      if (data.type === 'session_status_change') {
        console.log('Session status change detected, updating session state');
        setSession(prevSession => {
          if (!prevSession) return prevSession;
          
          return {
            ...prevSession,
            status: data.status || prevSession.status,
            completed_at_us: data.status === 'completed' ? Date.now() * 1000 : prevSession.completed_at_us,
            final_analysis: data.final_analysis || prevSession.final_analysis,
            error_message: data.error_message || prevSession.error_message,
            // Update duration if we can calculate it
            duration_ms: data.status === 'completed' && prevSession.started_at_us ? 
              Math.round((Date.now() * 1000 - prevSession.started_at_us) / 1000) : 
              prevSession.duration_ms
          };
        });
        
        // No need to refetch - we have all the data we need from the WebSocket update
        console.log('Session state updated from WebSocket data, no refetch needed');
      } 
      // Handle batched timeline updates - add new timeline items without refetching
      else if (data.type === 'batched_session_updates' && data.updates) {
        console.log('Timeline batch update detected, adding timeline items');
        setSession(prevSession => {
          if (!prevSession) return prevSession;
          
          const newTimelineItems = data.updates.map((update: any) => ({
            id: `${update.timestamp}_${Math.random()}`, // Generate unique ID
            event_id: update.session_id || sessionId,
            type: update.type === 'llm_interaction' ? 'llm' : 'mcp',
            timestamp_us: new Date(update.timestamp).getTime() * 1000,
            step_description: update.step_description || 'Processing...',
            duration_ms: update.duration_ms || null,
            details: update.type === 'llm_interaction' ? {
              prompt: 'LLM Analysis',
              response: update.step_description || '',
              model_name: update.model_used || 'unknown',
              tokens_used: undefined,
              temperature: undefined
            } : {
              tool_name: update.tool_name || 'unknown',
              parameters: {},
              result: update.step_description || '',
              server_name: update.server_name || 'unknown',
              execution_time_ms: update.duration_ms || 0
            }
          }));
          
          // Add new items to existing timeline, avoiding duplicates
          const existingTimestamps = new Set(prevSession.chronological_timeline.map((item: any) => item.timestamp_us));
          const uniqueNewItems = newTimelineItems.filter((item: any) => !existingTimestamps.has(item.timestamp_us));
          
          return {
            ...prevSession,
            chronological_timeline: [...prevSession.chronological_timeline, ...uniqueNewItems].sort((a: any, b: any) => a.timestamp_us - b.timestamp_us),
            llm_interaction_count: (prevSession.llm_interaction_count || 0) + uniqueNewItems.filter((item: any) => item.type === 'llm').length,
            mcp_communication_count: (prevSession.mcp_communication_count || 0) + uniqueNewItems.filter((item: any) => item.type === 'mcp').length
          };
        });
      }
      // Handle individual timeline interactions (fallback) - rarely used now
      else if (data.interaction_type === 'llm' || data.interaction_type === 'mcp') {
        console.log('Individual timeline interaction detected, adding timeline item');
        // Similar logic as above but for single item - implementation omitted for brevity
        // In practice, this case should rarely be hit since we use batched updates
        fetchSessionDetail(sessionId);
      } 
      // Handle any other session-specific updates - log and potentially ignore
      else {
        console.log('Other session-specific update type:', data.type, '- ignoring to prevent unnecessary refetch');
      }
    };

    // Handle session completion - refresh full session data to get final analysis and timeline
    const handleSessionCompleted = (update: SessionUpdate) => {
      console.log('SessionDetailPage received session completed:', update);
      
      // Only process updates for the current session
      if (update.session_id === sessionId) {
        console.log('Current session completed, refreshing full session data');
        // Fetch fresh session data to get final analysis and complete timeline
        fetchSessionDetail(sessionId);
      }
    };

    // Handle session failure - refresh full session data to get error details
    const handleSessionFailed = (update: SessionUpdate) => {
      console.log('SessionDetailPage received session failed:', update);
      
      // Only process updates for the current session
      if (update.session_id === sessionId) {
        console.log('Current session failed, refreshing full session data');
        // Fetch fresh session data to get error details and final state
        fetchSessionDetail(sessionId);
      }
    };

    // Subscribe to WebSocket events
    const unsubscribeUpdate = webSocketService.onSessionUpdate(handleSessionUpdate);
    const unsubscribeCompleted = webSocketService.onSessionCompleted(handleSessionCompleted);
    const unsubscribeFailed = webSocketService.onSessionFailed(handleSessionFailed);

    // Subscribe to session-specific channel for timeline updates
    const sessionChannel = `session_${sessionId}`;
    const unsubscribeSessionSpecific = webSocketService.onSessionSpecificUpdate(
      sessionChannel, 
      handleSessionSpecificUpdate
    );

    // Connect to WebSocket and subscribe to session-specific channel
    webSocketService.connect();
    webSocketService.subscribeToSessionChannel(sessionId);

    // Cleanup subscriptions
    return () => {
      console.log('SessionDetailPage cleaning up WebSocket subscriptions');
      unsubscribeUpdate();
      unsubscribeCompleted();
      unsubscribeFailed();
      unsubscribeSessionSpecific();
      
      // Unsubscribe from session-specific channel
      webSocketService.unsubscribeFromSessionChannel(sessionId);
    };
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