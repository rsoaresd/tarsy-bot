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
    if (onClick && session.id) {
      onClick(session.id);
    }
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
            sx={{ fontWeight: 500 }}
          />

          {/* Alert Information */}
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography 
              variant="body1" 
              sx={{ 
                fontWeight: 600,
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
              }}
            >
              {session.alert_type}
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ 
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
              }}
            >
              {session.agent_type} agent
            </Typography>
          </Box>

          {/* Duration */}
          <Box sx={{ textAlign: 'right', minWidth: '60px' }}>
            <Typography 
              variant="body2" 
              sx={{ 
                fontWeight: 500,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              }}
            >
              {formatDuration(currentDuration)}
            </Typography>
          </Box>

          {/* Progress Bar (only for in_progress status) */}
          {session.status === 'in_progress' && progress !== undefined && (
            <Box sx={{ minWidth: 100 }}>
              <LinearProgress
                variant="determinate"
                value={Math.min(progress, 100)}
                sx={{
                  height: 6,
                  borderRadius: 3,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 3,
                  },
                }}
              />
              <Typography 
                variant="caption" 
                color="text.secondary"
                sx={{ 
                  fontSize: '0.7rem',
                  display: 'block',
                  textAlign: 'center',
                  mt: 0.5,
                }}
              >
                {Math.round(progress)}%
              </Typography>
            </Box>
          )}
        </Box>

        {/* Error Message (if any) */}
        {session.error_message && (
          <Box sx={{ mt: 1, p: 1, bgcolor: 'error.50', borderRadius: 1 }}>
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
        {session.summary && (
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