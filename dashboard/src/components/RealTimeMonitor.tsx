import React from 'react';
import { Box, Typography, Chip, Tooltip } from '@mui/material';
import { Sync, AccessTime, Error as ErrorIcon } from '@mui/icons-material';
import { useWebSocketStatus, useDashboardUpdates } from '../hooks/useWebSocket';
import { formatDistanceToNow } from 'date-fns';
import ConnectionStatus from './ConnectionStatus';

interface StatusCount {
  active: number;
  completed: number;
  failed: number;
}

interface RealTimeMonitorProps {
  statusCounts: StatusCount;
  lastUpdate?: Date;
  autoRefreshEnabled: boolean;
}

function RealTimeMonitor({ statusCounts, lastUpdate, autoRefreshEnabled }: RealTimeMonitorProps) {
  const { 
    state, 
    isConnected, 
    error: wsError,
    stats,
    forceReconnect 
  } = useWebSocketStatus();
  
  const { 
    isSubscribed, 
    updates, 
    error: updatesError 
  } = useDashboardUpdates();

  // Determine connection status
  const getConnectionStatus = () => {
    if (!navigator.onLine) {
      return { status: 'disconnected' as const, errorMessage: 'No internet connection' };
    }
    
    if (state === 'connecting') {
      return { status: 'connecting' as const, errorMessage: null };
    }
    
    if (state === 'connected' && isConnected) {
      return { status: 'connected' as const, errorMessage: null };
    }
    
    if (wsError || updatesError) {
      const errorMessage = wsError?.message || updatesError || 'Connection error';
      return { status: 'error' as const, errorMessage };
    }
    
    return { status: 'disconnected' as const, errorMessage: 'Disconnected from server' };
  };

  const connectionInfo = getConnectionStatus();

  const handleRetry = async () => {
    try {
      await forceReconnect();
    } catch (error) {
      console.error('Manual reconnection failed:', error);
    }
  };

  // Format last update time
  const formatLastUpdate = (date?: Date) => {
    if (!date) return 'Never';
    try {
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  };

  // Calculate total sessions
  const totalSessions = statusCounts.active + statusCounts.completed + statusCounts.failed;

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 2,
        mb: 3,
        p: 2,
        backgroundColor: 'background.paper',
        borderRadius: 1,
        border: 1,
        borderColor: 'divider',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}
    >
      {/* Title and Connection Status */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
          Tarsy Dashboard
        </Typography>
        
        <ConnectionStatus
          status={connectionInfo.status}
          errorMessage={connectionInfo.errorMessage}
          onRetry={connectionInfo.status === 'error' ? handleRetry : undefined}
        />
      </Box>

      {/* Live Status Counters */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Tooltip title="Active Sessions" arrow>
          <Chip
            label={`${statusCounts.active} Active`}
            color="info"
            size="medium"
            sx={{ 
              fontWeight: 600,
              '& .MuiChip-label': {
                fontSize: '0.95rem',
              },
            }}
            aria-label={`${statusCounts.active} active sessions`}
          />
        </Tooltip>

        <Tooltip title="Completed Sessions" arrow>
          <Chip
            label={`${statusCounts.completed} Completed`}
            color="success"
            size="medium"
            sx={{ 
              fontWeight: 600,
              '& .MuiChip-label': {
                fontSize: '0.95rem',
              },
            }}
            aria-label={`${statusCounts.completed} completed sessions`}
          />
        </Tooltip>

        <Tooltip title="Failed Sessions" arrow>
          <Chip
            label={`${statusCounts.failed} Failed`}
            color="error"
            size="medium"
            sx={{ 
              fontWeight: 600,
              '& .MuiChip-label': {
                fontSize: '0.95rem',
              },
            }}
            aria-label={`${statusCounts.failed} failed sessions`}
          />
        </Tooltip>

        <Tooltip title="Total Sessions" arrow>
          <Chip
            label={`${totalSessions} Total`}
            color="default"
            size="medium"
            sx={{ 
              fontWeight: 600,
              '& .MuiChip-label': {
                fontSize: '0.95rem',
              },
            }}
            aria-label={`${totalSessions} total sessions`}
          />
        </Tooltip>
      </Box>

      {/* Auto-refresh and Last Update */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Auto-refresh Indicator */}
        {autoRefreshEnabled && connectionInfo.status === 'connected' && (
          <Tooltip title="Auto-refresh enabled" arrow>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <Sync
                sx={{
                  fontSize: 16,
                  color: 'success.main',
                  animation: 'spin 2s linear infinite',
                  '@keyframes spin': {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' },
                  },
                }}
              />
              <Typography variant="body2" color="success.main" sx={{ fontWeight: 500 }}>
                Live
              </Typography>
            </Box>
          </Tooltip>
        )}

        {/* Last Update Time */}
        <Tooltip title={`Last updated: ${lastUpdate?.toLocaleString() || 'Never'}`} arrow>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <AccessTime sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">
              {formatLastUpdate(lastUpdate)}
            </Typography>
          </Box>
        </Tooltip>

        {/* Connection Stats (Development Mode) */}
        {process.env.NODE_ENV === 'development' && stats && (
          <Tooltip
            title={
              <Box>
                <Typography variant="body2">Connection Stats:</Typography>
                <Typography variant="caption">
                  Reconnections: {stats.totalReconnections}
                </Typography>
                <br />
                <Typography variant="caption">
                  Messages: {stats.messagesReceived}/{stats.messagesSent}
                </Typography>
                <br />
                <Typography variant="caption">
                  Queue: {stats.queueStats.size} ({stats.queueStats.highPriority} priority)
                </Typography>
              </Box>
            }
            arrow
          >
            <Chip
              size="small"
              label={`${stats.subscriptionCount} subs`}
              sx={{ fontSize: '0.7rem' }}
            />
          </Tooltip>
        )}

        {/* Error Indicator */}
        {(wsError || updatesError) && (
          <Tooltip title={wsError?.message || updatesError || 'Connection error'} arrow>
            <ErrorIcon color="error" sx={{ fontSize: 20 }} />
          </Tooltip>
        )}
      </Box>

      {/* Offline Banner */}
      {!navigator.onLine && (
        <Box
          sx={{
            width: '100%',
            mt: 1,
            p: 1,
            backgroundColor: 'warning.light',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <ErrorIcon sx={{ color: 'warning.dark', fontSize: 18 }} />
          <Typography variant="body2" color="warning.dark" sx={{ fontWeight: 500 }}>
            You are offline. Some features may be limited.
          </Typography>
        </Box>
      )}

      {/* ARIA Live Region for Screen Readers */}
      <Box
        role="status"
        aria-live="polite"
        aria-label="Connection status and live updates"
        sx={{
          position: 'absolute',
          left: -10000,
          width: 1,
          height: 1,
          overflow: 'hidden',
        }}
      >
        {connectionInfo.status === 'connected' 
          ? 'Connected to dashboard updates' 
          : `Connection ${connectionInfo.status}${connectionInfo.errorMessage ? ': ' + connectionInfo.errorMessage : ''}`
        }
        {updates && `, Last update: ${formatLastUpdate(lastUpdate)}`}
      </Box>
    </Box>
  );
}

export default RealTimeMonitor; 