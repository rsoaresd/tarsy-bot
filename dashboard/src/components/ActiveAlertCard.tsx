import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
} from '@mui/material';
import {
  Error,
  Warning,
  Refresh,
  Schedule,
} from '@mui/icons-material';
import type { ActiveAlertCardProps } from '../types';

// Helper function to format duration from milliseconds
const formatDuration = (durationMs: number | null): string => {
  if (!durationMs) return '0s';
  
  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${Math.floor(durationMs / 1000)}s`;
  
  const minutes = Math.floor(durationMs / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

// Helper function to get status chip configuration
const getStatusChipConfig = (status: string) => {
  switch (status) {
    case 'in_progress':
      return {
        color: 'info' as const,
        icon: <Refresh sx={{ fontSize: 16 }} />,
        label: 'In Progress',
      };
    case 'pending':
      return {
        color: 'warning' as const,
        icon: <Schedule sx={{ fontSize: 16 }} />,
        label: 'Pending',
      };
    case 'failed':
      return {
        color: 'error' as const,
        icon: <Error sx={{ fontSize: 16 }} />,
        label: 'Failed',
      };
    default:
      return {
        color: 'default' as const,
        icon: <Warning sx={{ fontSize: 16 }} />,
        label: status,
      };
  }
};

// Animation styles for processing alerts
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
 * ActiveAlertCard component displays an individual active alert
 * with progress indicators and real-time status updates
 */
const ActiveAlertCard: React.FC<ActiveAlertCardProps> = ({ 
  session, 
  progress, 
  onClick 
}) => {
  const statusConfig = getStatusChipConfig(session.status);
  
  // Calculate duration from start time to now (for ongoing sessions)
  const currentDuration = session.duration_ms || (
    Date.now() - new Date(session.started_at).getTime()
  );

  const handleCardClick = () => {
    if (onClick && session.session_id) {
      onClick(session.session_id);
    }
  };

  // Apply breathing glow animation for processing alerts
  const getAnimationStyle = () => {
    if (session.status !== 'in_progress') return {};
    return animationStyles.breathingGlow;
  };

  return (
    <Card 
      variant="outlined" 
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick ? {
          boxShadow: 2,
          transform: 'translateY(-2px)',
        } : {},
        ...getAnimationStyle(), // Apply animation for in-progress status
      }}
      onClick={handleCardClick}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Status Chip */}
          <Chip
            color={statusConfig.color}
            icon={statusConfig.icon}
            label={statusConfig.label}
            size="small"
            sx={{ 
              fontWeight: 500,
              minWidth: 120,
            }}
          />

          {/* Alert Type */}
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 600,
              flex: 1,
              textAlign: 'center',
            }}
          >
            {session.alert_type}
          </Typography>

          {/* Duration */}
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              fontFamily: 'monospace',
              minWidth: 60,
              textAlign: 'right',
            }}
          >
            {formatDuration(currentDuration)}
          </Typography>
        </Box>

        {/* Progress Bar for in_progress sessions */}
        {session.status === 'in_progress' && (
          <Box sx={{ mt: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Processing Progress
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {progress !== undefined ? `${progress}%` : 'Unknown'}
              </Typography>
            </Box>
            <LinearProgress 
              variant={progress !== undefined ? "determinate" : "indeterminate"}
              value={progress}
              sx={{
                height: 3,
                borderRadius: 2,
                backgroundColor: 'rgba(0, 0, 0, 0.04)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 2,
                  backgroundColor: 'rgba(2, 136, 209, 0.6)',
                },
              }}
            />
          </Box>
        )}

        {/* Agent Type */}
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Agent: {session.agent_type}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Started: {new Date(session.started_at).toLocaleTimeString()}
          </Typography>
        </Box>

        {/* Error Message (for failed sessions) */}
        {session.status === 'failed' && session.error_message && (
          <Box sx={{ mt: 2, p: 1, bgcolor: 'error.light', borderRadius: 1, border: '1px solid', borderColor: 'error.main' }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Error:
            </Typography>
            <Typography 
              variant="caption" 
              color="error.main"
              sx={{ 
                display: 'block',
                fontFamily: 'monospace',
                fontSize: '0.75rem',
              }}
            >
              {session.error_message}
            </Typography>
          </Box>
        )}

        {/* Summary (if available) */}
        {session.summary && typeof session.summary === 'string' && session.summary.trim() && (
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ 
              mt: 1,
              textOverflow: 'ellipsis',
              overflow: 'hidden',
              whiteSpace: 'nowrap',
            }}
          >
            {session.summary}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};

export default ActiveAlertCard; 