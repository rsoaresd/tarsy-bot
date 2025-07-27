import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Error,
  Warning,
  Refresh,
  Schedule,
  OpenInNew,
} from '@mui/icons-material';
import type { ActiveAlertCardProps } from '../types';
import { formatTimestamp, formatDuration, getCurrentTimestampUs } from '../utils/timestamp';

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
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 8px 1px rgba(2, 136, 209, 0.2)'
      },
      '50%': { 
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 24px 4px rgba(2, 136, 209, 0.45)'
      },
      '100%': { 
        boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24), 0 0 8px 1px rgba(2, 136, 209, 0.2)'
      },
    },
    animation: 'breathingGlow 2.8s ease-in-out infinite',
  },
};

/**
 * ActiveAlertCard component displays an individual active alert
 * with progress indicators and real-time status updates.
 * Uses Unix timestamp utilities for optimal performance and consistency.
 */
const ActiveAlertCard: React.FC<ActiveAlertCardProps> = ({ 
  session, 
  progress, 
  onClick 
}) => {
  const statusConfig = getStatusChipConfig(session.status);
  
  // Calculate duration from start time to now (for ongoing sessions)
  const currentDuration = session.completed_at_us 
    ? formatDuration(session.started_at_us, session.completed_at_us)
    : formatDuration(session.started_at_us, getCurrentTimestampUs());

  // Handle card click (same tab navigation)
  const handleCardClick = () => {
    if (onClick && session.session_id) {
      onClick(session.session_id);
    }
  };

  // Handle new tab icon click
  const handleNewTabClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    if (session.session_id) {
      const url = `${window.location.origin}/sessions/${session.session_id}`;
      window.open(url, '_blank');
    }
  };

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s ease-in-out',
        '&:hover': onClick ? {
          transform: 'translateY(-1px)',
          boxShadow: 4,
        } : {},
        ...(session.status === 'in_progress' ? animationStyles.breathingGlow : {}),
        position: 'relative',
      }}
      onClick={handleCardClick}
    >
      <CardContent sx={{ pb: 2 }}>
        {/* Header with status and new tab icon */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
            <Chip
              icon={statusConfig.icon}
              label={statusConfig.label}
              color={statusConfig.color}
              size="small"
              sx={{ fontWeight: 500 }}
            />
            <Typography variant="body2" color="text.secondary">
              {session.agent_type}
            </Typography>
          </Box>
          
          {/* New Tab Icon */}
          <Tooltip title="Open in new tab">
            <IconButton
              size="small"
              onClick={handleNewTabClick}
              sx={{
                opacity: 0.7,
                '&:hover': {
                  opacity: 1,
                  backgroundColor: 'action.hover',
                },
              }}
            >
              <OpenInNew fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Alert Type Title */}
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 600,
            mb: 1,
          }}
        >
          {session.alert_type}
        </Typography>

        {/* Time and Duration */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Started: {formatTimestamp(session.started_at_us, 'time-only')}
          </Typography>
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ fontFamily: 'monospace' }}
          >
            {currentDuration}
          </Typography>
        </Box>

        {/* Progress Bar for in_progress sessions */}
        {session.status === 'in_progress' && (
          <Box sx={{ mb: 2 }}>
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

        {/* Error Message (for failed sessions) */}
        {session.status === 'failed' && session.error_message && (
          <Box sx={{ mt: 1, p: 1, bgcolor: 'error.light', borderRadius: 1, border: '1px solid', borderColor: 'error.main' }}>
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