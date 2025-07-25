import React, { useState, useEffect, useCallback } from 'react';
import { Box, Alert, CircularProgress, Snackbar } from '@mui/material';
import { useParams } from 'react-router-dom';
import { useSessionUpdates, useWebSocketCleanup } from '../hooks/useWebSocket';
import { dashboardApi, formatApiError } from '../services/api';
import SessionHeader from './SessionHeader';
import SessionActions from './SessionActions';
import TimelineVisualization from './TimelineVisualization';
import InteractionDetails from './InteractionDetails';
import { SessionSummary, InteractionDetail, SessionTimeline } from '../types';

function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  
  // State management
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [timeline, setTimeline] = useState<SessionTimeline | null>(null);
  const [selectedInteraction, setSelectedInteraction] = useState<InteractionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isActive, setIsActive] = useState(false);

  // WebSocket integration for real-time updates  
  const { 
    isSubscribed, 
    updates: wsUpdates, 
    error: wsError 
  } = useSessionUpdates(sessionId || '', undefined, { enabled: isActive });

  // Cleanup WebSocket on unmount
  useWebSocketCleanup();

  // Load session data
  const loadSessionData = useCallback(async () => {
    if (!sessionId) {
      setError('No session ID provided');
      setIsLoading(false);
      return;
    }

    try {
      setError(null);
      setIsLoading(true);

      // Load session summary and timeline in parallel
      const [sessionResult, timelineResult] = await Promise.all([
        dashboardApi.getSessionSummary(sessionId),
        dashboardApi.getSessionTimeline(sessionId),
      ]);

      setSession(sessionResult);
      setTimeline(timelineResult);
      
      // Determine if session is active based on status
      const isSessionActive = ['processing', 'pending'].includes(sessionResult.status);
      setIsActive(isSessionActive);

    } catch (err) {
      console.error('Failed to load session data:', err);
      setError(formatApiError(err));
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Handle interaction selection from timeline
  const handleInteractionClick = useCallback((interaction: InteractionDetail) => {
    setSelectedInteraction(interaction);
  }, []);

  // Handle refresh for active sessions
  const handleRefresh = useCallback(() => {
    loadSessionData();
  }, [loadSessionData]);

  // Initial data load
  useEffect(() => {
    loadSessionData();
  }, [loadSessionData]);

  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      setError(`WebSocket error: ${wsError}`);
    }
  }, [wsError]);

  // Loading state
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Error state
  if (error || !session || !timeline) {
    return (
      <Box>
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          action={
            <button onClick={loadSessionData}>
              Retry
            </button>
          }
        >
          {error || 'Failed to load session data'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Session Header */}
      <SessionHeader 
        session={session} 
        isActive={isActive}
      />

      {/* Session Actions */}
      <SessionActions
        session={session}
        interactions={timeline.interactions}
        isActive={isActive}
        onRefresh={handleRefresh}
      />

      {/* Timeline Visualization */}
      <TimelineVisualization
        interactions={timeline.interactions}
        isActive={isActive}
        onInteractionClick={handleInteractionClick}
        height={500}
      />

      {/* Interaction Details */}
      <InteractionDetails
        interaction={selectedInteraction}
        allInteractions={timeline.interactions}
      />

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      {/* Real-time Status Indicator */}
      {isActive && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000,
          }}
        >
          <Alert
            severity="info"
            sx={{
              backgroundColor: 'primary.main',
              color: 'primary.contrastText',
              '& .MuiAlert-icon': {
                color: 'primary.contrastText',
              },
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  backgroundColor: 'success.main',
                  animation: 'pulse 2s infinite',
                  '@keyframes pulse': {
                    '0%': { opacity: 1 },
                    '50%': { opacity: 0.5 },
                    '100%': { opacity: 1 },
                  },
                }}
                aria-hidden="true"
              />
              Live Session - Updates in real-time
            </Box>
          </Alert>
        </Box>
      )}

      {/* ARIA Live Region for Screen Readers */}
      {isActive && (
        <Box
          aria-live="polite"
          aria-atomic="false"
          style={{
            position: 'absolute',
            left: '-10000px',
            width: '1px',
            height: '1px',
            overflow: 'hidden',
          }}
        >
          Session {sessionId} is active. Timeline has {timeline.interactions.length} interactions.
          {selectedInteraction && ` Selected interaction: ${selectedInteraction.step_description}`}
        </Box>
      )}
    </Box>
  );
}

export default SessionDetailPage; 