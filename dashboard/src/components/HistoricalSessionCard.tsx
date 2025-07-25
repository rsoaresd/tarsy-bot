import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  Warning as TimeoutIcon,
  Schedule as PendingIcon,
  Visibility as ViewIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { SessionSummary } from '../types';

interface HistoricalSessionCardProps {
  session: SessionSummary;
  onClick: () => void;
}

function HistoricalSessionCard({ session, onClick }: HistoricalSessionCardProps) {
  const theme = useTheme();

  // Get status display configuration
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          icon: <CompletedIcon />,
          color: theme.palette.success.main,
          bgColor: theme.palette.success.light,
          label: 'Completed',
        };
      case 'error':
        return {
          icon: <ErrorIcon />,
          color: theme.palette.error.main,
          bgColor: theme.palette.error.light,
          label: 'Failed',
        };
      case 'timeout':
        return {
          icon: <TimeoutIcon />,
          color: theme.palette.warning.main,
          bgColor: theme.palette.warning.light,
          label: 'Timeout',
        };
      default:
        return {
          icon: <PendingIcon />,
          color: theme.palette.grey[500],
          bgColor: theme.palette.grey[200],
          label: 'Pending',
        };
    }
  };

  // Format duration
  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime || !endTime) return 'Unknown';
    
    const start = new Date(startTime);
    const end = new Date(endTime);
    const durationMs = end.getTime() - start.getTime();
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) return `${durationSeconds}s`;
    if (durationSeconds < 3600) return `${Math.floor(durationSeconds / 60)}m ${durationSeconds % 60}s`;
    return `${Math.floor(durationSeconds / 3600)}h ${Math.floor((durationSeconds % 3600) / 60)}m`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unknown time';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    // Show relative time for recent items
    if (diffMs < 24 * 60 * 60 * 1000) { // Less than 24 hours
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
    }
    
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  const statusDisplay = getStatusDisplay(session.status);

  return (
    <Card
      sx={{
        cursor: 'pointer',
        transition: 'all 0.2s ease-in-out',
        '&:hover': {
          boxShadow: theme.shadows[4],
          transform: 'translateY(-2px)',
        },
        '&:active': {
          transform: 'translateY(0px)',
        },
      }}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
      aria-label={`View session ${session.session_id} details`}
    >
      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
        {/* Header Row */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          {/* Status and Session ID */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={statusDisplay.icon}
              label={statusDisplay.label}
              size="small"
              sx={{
                backgroundColor: statusDisplay.bgColor,
                color: statusDisplay.color,
                '& .MuiChip-icon': {
                  color: statusDisplay.color,
                },
              }}
            />
            
            <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace' }}>
              {session.session_id.slice(-8)}
            </Typography>
          </Box>

          {/* Action Button */}
          <Tooltip title="View details" arrow>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onClick();
              }}
              aria-label="View session details"
            >
              <ViewIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Agent Type and Current Step */}
        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 500 }} noWrap>
            {session.current_step || 'No description available'}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Chip
              label={session.agent_type || 'Unknown'}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.75rem', height: 20 }}
            />
          </Box>
        </Box>

        {/* Metadata Row */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr 1fr',
          gap: 1,
          fontSize: '0.75rem',
          color: 'text.secondary',
        }}>
          {/* Duration */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TimeIcon sx={{ fontSize: 14 }} />
            <Typography variant="caption">
              {formatDuration(session.start_time, session.last_activity)}
            </Typography>
          </Box>

          {/* Interactions Count */}
          <Box>
            <Typography variant="caption">
              {session.interactions_count} interactions
            </Typography>
          </Box>

          {/* Timestamp */}
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="caption">
              {formatTimestamp(session.start_time)}
            </Typography>
          </Box>
        </Box>

        {/* Error Indicator */}
        {session.errors_count > 0 && (
          <Box sx={{ mt: 1 }}>
            <Chip
              label={`${session.errors_count} error${session.errors_count > 1 ? 's' : ''}`}
              size="small"
              color="error"
              variant="outlined"
              sx={{ fontSize: '0.75rem', height: 20 }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export default React.memo(HistoricalSessionCard); 