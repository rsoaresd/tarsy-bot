import { Paper, Typography, Box } from '@mui/material';
import StatusBadge from './StatusBadge';
import type { SessionHeaderProps } from '../types';

/**
 * Utility function to format timestamp for display
 */
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch (error) {
    return timestamp;
  }
};

/**
 * Utility function to format duration in milliseconds
 */
const formatDuration = (durationMs: number | null): string => {
  if (!durationMs) return '-';
  
  if (durationMs < 1000) {
    return `${durationMs}ms`;
  } else if (durationMs < 60000) {
    return `${(durationMs / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(durationMs / 60000);
    const seconds = Math.floor((durationMs % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
};

// Animation styles for processing sessions
const animationStyles = {
  breathingGlow: {
    '@keyframes breathingGlow': {
      '0%': { 
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 0 0 rgba(2, 136, 209, 0.1)'
      },
      '50%': { 
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 12px 2px rgba(2, 136, 209, 0.25)'
      },
      '100%': { 
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 0 0 rgba(2, 136, 209, 0.1)'
      },
    },
    animation: 'breathingGlow 2.8s ease-in-out infinite',
  },
};

/**
 * SessionHeader component - Phase 3
 * Displays session metadata including status, timing, and summary information
 */
function SessionHeader({ session }: SessionHeaderProps) {
  // Apply breathing glow animation for processing sessions
  const getAnimationStyle = () => {
    if (session.status !== 'in_progress') return {};
    return animationStyles.breathingGlow;
  };

  return (
    <Paper sx={{ 
      p: 3,
      ...getAnimationStyle(), // Apply animation for in-progress status
    }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        {/* Status Badge */}
        <Box>
          <StatusBadge status={session.status} size="medium" />
        </Box>

        {/* Session ID and Summary */}
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
            {session.session_id}
            {session.status === 'in_progress' && (
              <Typography component="span" variant="body2" color="info.main" sx={{ ml: 2, fontWeight: 400 }}>
                • Processing...
              </Typography>
            )}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {session.alert_type} • {session.agent_type} agent • Started at {formatTimestamp(session.started_at)}
          </Typography>
          {session.summary && typeof session.summary === 'string' && session.summary.trim() && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {session.summary}
            </Typography>
          )}
        </Box>

        {/* Duration and Completion Info */}
        <Box sx={{ textAlign: 'right', minWidth: 120 }}>
          <Typography 
            variant="h6" 
            color={session.status === 'completed' ? 'success.main' : 'text.primary'}
            sx={{ fontWeight: 600 }}
          >
            Duration: {formatDuration(session.duration_ms)}
          </Typography>
          {session.completed_at && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              Completed at {formatTimestamp(session.completed_at)}
            </Typography>
          )}
          {session.status === 'in_progress' && (
            <Typography variant="body2" color="info.main" sx={{ mt: 0.5 }}>
              Currently processing...
            </Typography>
          )}
        </Box>
      </Box>
    </Paper>
  );
}

export default SessionHeader; 