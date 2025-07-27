import { useState, useEffect } from 'react';
import { Container, AppBar, Toolbar, Typography, Box, Tooltip, CircularProgress, IconButton } from '@mui/material';
import { FiberManualRecord, Refresh } from '@mui/icons-material';
import DashboardLayout from './DashboardLayout';
import { apiClient, handleAPIError } from '../services/api';
import { webSocketService } from '../services/websocket';
import type { Session, SessionUpdate } from '../types';

/**
 * DashboardView component for the Tarsy Dashboard - Phase 3
 * Contains the main dashboard logic moved from App.tsx with navigation support
 */
function DashboardView() {
  // Active alerts state
  const [activeAlerts, setActiveAlerts] = useState<Session[]>([]);
  const [activeLoading, setActiveLoading] = useState<boolean>(true);
  const [activeError, setActiveError] = useState<string | null>(null);

  // Historical alerts state
  const [historicalAlerts, setHistoricalAlerts] = useState<Session[]>([]);
  const [historicalLoading, setHistoricalLoading] = useState<boolean>(true);
  const [historicalError, setHistoricalError] = useState<string | null>(null);

  // WebSocket connection state
  const [wsConnected, setWsConnected] = useState<boolean>(false);

  // Fetch active sessions
  const fetchActiveAlerts = async () => {
    try {
      setActiveLoading(true);
      setActiveError(null);
      const response = await apiClient.getActiveSessions();
      setActiveAlerts(response.active_sessions);
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setActiveError(errorMessage);
      console.error('Failed to fetch active sessions:', err);
    } finally {
      setActiveLoading(false);
    }
  };

  // Fetch historical sessions
  const fetchHistoricalAlerts = async () => {
    try {
      setHistoricalLoading(true);
      setHistoricalError(null);
      const response = await apiClient.getHistoricalSessions();
      setHistoricalAlerts(response.sessions);
    } catch (err) {
      const errorMessage = handleAPIError(err);
      setHistoricalError(errorMessage);
      console.error('Failed to fetch historical sessions:', err);
    } finally {
      setHistoricalLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchActiveAlerts();
    fetchHistoricalAlerts();
  }, []);

  // Set up WebSocket event handlers for real-time updates
  useEffect(() => {
    const handleSessionUpdate = (update: SessionUpdate) => {
      console.log('DashboardView received session update:', update);
      // Update active alerts if the session is still active
      setActiveAlerts(prev => 
        prev.map(session => 
          session.session_id === update.session_id 
            ? { ...session, status: update.status, duration_ms: update.duration_ms || session.duration_ms }
            : session
        )
      );
    };

    const handleSessionCompleted = (update: SessionUpdate) => {
      console.log('DashboardView received session completed:', update);
      // Remove from active alerts and add to historical alerts
      setActiveAlerts(prev => prev.filter(session => session.session_id !== update.session_id));
      
      // Refresh historical alerts to include the newly completed session
      fetchHistoricalAlerts();
    };

    const handleSessionFailed = (update: SessionUpdate) => {
      console.log('DashboardView received session failed:', update);
      // Remove from active alerts and add to historical alerts
      setActiveAlerts(prev => prev.filter(session => session.session_id !== update.session_id));
      
      // Refresh historical alerts to include the newly failed session
      fetchHistoricalAlerts();
    };

    // WebSocket error handler
    const handleWebSocketError = (error: Event) => {
      console.warn('WebSocket connection error - real-time updates unavailable:', error);
      console.log('💡 Use manual refresh buttons if needed');
      setWsConnected(false); // Update connection status immediately
    };

    // WebSocket close handler  
    const handleWebSocketClose = (event: CloseEvent) => {
      console.warn('WebSocket connection closed - real-time updates unavailable:', {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
      console.log('💡 Use manual refresh buttons if needed');
      setWsConnected(false); // Update connection status immediately
    };

    // Dashboard update handler - handles real-time dashboard updates from backend
    const handleDashboardUpdate = (update: any) => {
      console.log('📊 Real-time dashboard update received:', update);
      
      // Only refresh data if there are actual changes to sessions
      if (update.type === 'system_metrics' && update.active_sessions_list) {
        const newActiveCount = update.active_sessions_list.length;
        const currentActiveCount = activeAlerts.length;
        
        // Only refresh if the number of active sessions changed
        if (newActiveCount !== currentActiveCount) {
          console.log(`🔄 Active sessions changed: ${currentActiveCount} → ${newActiveCount}, refreshing data`);
          fetchActiveAlerts();
          fetchHistoricalAlerts();
        } else {
          console.log('📊 System metrics update - no session changes, skipping refresh');
        }
      } else {
        // For non-system-metrics updates, always refresh
        console.log('🔄 Non-metrics update - refreshing dashboard data');
        fetchActiveAlerts();
        fetchHistoricalAlerts();
      }
    };

    // Connection change handler - updates UI immediately when WebSocket connection changes
    const handleConnectionChange = (connected: boolean) => {
      setWsConnected(connected);
      if (connected) {
        console.log('✅ WebSocket connected - real-time updates active');
      } else {
        console.log('❌ WebSocket disconnected - use manual refresh buttons');
      }
    };

    // Subscribe to WebSocket events
    const unsubscribeUpdate = webSocketService.onSessionUpdate(handleSessionUpdate);
    const unsubscribeCompleted = webSocketService.onSessionCompleted(handleSessionCompleted);
    const unsubscribeFailed = webSocketService.onSessionFailed(handleSessionFailed);
    const unsubscribeDashboard = webSocketService.onDashboardUpdate(handleDashboardUpdate);
    const unsubscribeConnection = webSocketService.onConnectionChange(handleConnectionChange);
    const unsubscribeError = webSocketService.onError(handleWebSocketError);
    const unsubscribeClose = webSocketService.onClose(handleWebSocketClose);

    // Connect to WebSocket with enhanced logging
    console.log('🔌 Connecting to WebSocket for real-time updates...');
    webSocketService.connect();

    // Set initial connection status
    setWsConnected(webSocketService.isConnected);

    // Cleanup
    return () => {
      console.log('DashboardView cleaning up WebSocket subscriptions');
      unsubscribeUpdate();
      unsubscribeCompleted();
      unsubscribeFailed();
      unsubscribeDashboard();
      unsubscribeConnection();
      unsubscribeError();
      unsubscribeClose();
    };
  }, []);

  // Phase 3: Handle session click with navigation in new tab
  const handleSessionClick = (sessionId: string) => {
    console.log('Opening session detail in new tab:', sessionId);
    const url = `${window.location.origin}/sessions/${sessionId}`;
    window.open(url, '_blank');
  };

  // Handle refresh actions
  const handleRefreshActive = () => {
    fetchActiveAlerts();
  };

  const handleRefreshHistorical = () => {
    fetchHistoricalAlerts();
  };

  // Handle WebSocket retry
  const handleWebSocketRetry = () => {
    console.log('🔄 Manual WebSocket retry requested');
    webSocketService.retry();
  };

  return (
    <Container maxWidth={false} sx={{ px: 2 }}>
      {/* AppBar with dashboard title and live indicator */}
      <AppBar position="static" elevation={0} sx={{ borderRadius: 1 }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Tarsy Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {/* Connection Status Indicator */}
            <Tooltip 
              title={wsConnected 
                ? "Connected - Real-time updates active" 
                : "Disconnected - Use manual refresh buttons or retry connection"
              }
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <FiberManualRecord 
                  sx={{ 
                    fontSize: 12, 
                    color: wsConnected ? 'success.main' : 'error.main',
                    animation: wsConnected ? 'none' : 'pulse 2s infinite',
                    '@keyframes pulse': {
                      '0%': { opacity: 0.5 },
                      '50%': { opacity: 1 },
                      '100%': { opacity: 0.5 },
                    }
                  }} 
                />
                <Typography variant="body2" sx={{ color: 'inherit' }}>
                  {wsConnected ? 'Live' : 'Manual'}
                </Typography>
              </Box>
            </Tooltip>

            {/* WebSocket Retry Button - only show when disconnected */}
            {!wsConnected && (
              <Tooltip title="Retry WebSocket connection">
                <IconButton
                  size="small"
                  onClick={handleWebSocketRetry}
                  sx={{ 
                    color: 'inherit',
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    }
                  }}
                >
                  <Refresh fontSize="small" />
                </IconButton>
              </Tooltip>
            )}

            {/* Loading indicator for active refreshes */}
            {(activeLoading || historicalLoading) && (
              <Tooltip title="Loading data...">
                <CircularProgress size={20} sx={{ color: 'inherit' }} />
              </Tooltip>
            )}
          </Box>
        </Toolbar>
      </AppBar>

      {/* Main content area with two-section layout */}
      <Box sx={{ mt: 2 }}>
        <DashboardLayout
          activeAlerts={activeAlerts}
          historicalAlerts={historicalAlerts}
          activeLoading={activeLoading}
          historicalLoading={historicalLoading}
          activeError={activeError}
          historicalError={historicalError}
          onRefreshActive={handleRefreshActive}
          onRefreshHistorical={handleRefreshHistorical}
          onSessionClick={handleSessionClick}
        />
      </Box>
    </Container>
  );
}

export default DashboardView; 