import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Breadcrumbs,
  Link,
  Paper,
  Divider,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Home as HomeIcon,
  History as HistoryIcon,
  PlayArrow as ActiveIcon,
  CheckCircle as CompletedIcon,
  Error as ErrorIcon,
  Warning as TimeoutIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { SessionSummary } from '../types';

interface SessionHeaderProps {
  session: SessionSummary;
  isActive?: boolean;
}

function SessionHeader({ session, isActive = false }: SessionHeaderProps) {
  const theme = useTheme();
  const navigate = useNavigate();

  // Get status display configuration
  const getStatusDisplay = (status: string, isActive: boolean) => {
    if (isActive) {
      return {
        icon: <ActiveIcon sx={{ color: 'primary.main', fontSize: 20 }} />,
        color: 'primary.main',
        label: 'ACTIVE SESSION',
        bgColor: 'primary.light',
        textColor: 'primary.contrastText',
      };
    }

    switch (status) {
      case 'completed':
        return {
          icon: <CompletedIcon sx={{ color: 'success.main', fontSize: 20 }} />,
          color: 'success.main',
          label: 'COMPLETED',
          bgColor: 'success.light',
          textColor: 'success.contrastText',
        };
      case 'error':
        return {
          icon: <ErrorIcon sx={{ color: 'error.main', fontSize: 20 }} />,
          color: 'error.main',
          label: 'FAILED',
          bgColor: 'error.light',
          textColor: 'error.contrastText',
        };
      case 'timeout':
        return {
          icon: <TimeoutIcon sx={{ color: 'warning.main', fontSize: 20 }} />,
          color: 'warning.main',
          label: 'TIMEOUT',
          bgColor: 'warning.light',
          textColor: 'warning.contrastText',
        };
      default:
        return {
          icon: <PendingIcon sx={{ color: 'grey.500', fontSize: 20 }} />,
          color: 'grey.500',
          label: 'PENDING',
          bgColor: 'grey.200',
          textColor: 'grey.800',
        };
    }
  };

  // Format duration
  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return 'Unknown duration';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : (isActive ? new Date() : start);
    const durationMs = end.getTime() - start.getTime();
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) return `${durationSeconds}s`;
    if (durationSeconds < 3600) return `${Math.floor(durationSeconds / 60)}m ${durationSeconds % 60}s`;
    return `${Math.floor(durationSeconds / 3600)}h ${Math.floor((durationSeconds % 3600) / 60)}m`;
  };

  // Format timestamp
  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unknown time';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  const statusDisplay = getStatusDisplay(session.status, isActive);

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* Breadcrumb Navigation */}
      <Breadcrumbs 
        aria-label="Session detail breadcrumb navigation" 
        sx={{ mb: 2 }}
      >
        <Link
          component="button"
          variant="body2"
          onClick={() => navigate('/dashboard')}
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 0.5,
            textDecoration: 'none',
            color: 'primary.main',
            '&:hover': {
              textDecoration: 'underline',
            },
          }}
          aria-label="Back to dashboard"
        >
          <HomeIcon fontSize="small" />
          Dashboard
        </Link>
        
        <Typography 
          variant="body2" 
          color="text.primary"
          sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
        >
          <HistoryIcon fontSize="small" />
          Session {session.session_id}
        </Typography>
      </Breadcrumbs>

      {/* Session Title and Status */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box>
          <Typography variant="h1" component="h1" gutterBottom>
            Alert Details: {session.session_id}
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            {session.current_step || 'No description available'}
          </Typography>
        </Box>

        {/* Status Badge */}
        <Tooltip title={`Session is ${isActive ? 'currently active' : 'historical'}`} arrow>
          <Chip
            icon={statusDisplay.icon}
            label={statusDisplay.label}
            sx={{
              backgroundColor: statusDisplay.bgColor,
              color: statusDisplay.textColor,
              fontWeight: 600,
              fontSize: '0.875rem',
              height: 40,
              '& .MuiChip-icon': {
                color: statusDisplay.color,
              },
            }}
            aria-label={`Session status: ${statusDisplay.label}`}
          />
        </Tooltip>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Session Metadata */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: '1fr 1fr 1fr 1fr' },
        gap: 3,
      }}>
        {/* Agent Type */}
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Agent Type
          </Typography>
          <Chip
            label={session.agent_type || 'Unknown'}
            size="small"
            variant="outlined"
            sx={{ mt: 0.5 }}
          />
        </Box>

        {/* Start Time */}
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            {isActive ? 'Started At' : 'Processed At'}
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace', mt: 0.5 }}>
            {formatTimestamp(session.start_time)}
          </Typography>
        </Box>

        {/* Duration */}
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Duration
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'Roboto Mono, monospace', mt: 0.5 }}>
            {formatDuration(session.start_time, session.last_activity)}
          </Typography>
        </Box>

        {/* Interactions Count */}
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Interactions
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {session.interactions_count}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              ({session.llm_interactions} LLM, {session.mcp_communications} MCP)
            </Typography>
          </Box>
        </Box>

        {/* Progress (for active sessions) */}
        {isActive && (
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              Progress
            </Typography>
            <Typography variant="body2" sx={{ mt: 0.5 }}>
              {session.progress_percentage}%
            </Typography>
          </Box>
        )}

        {/* Error Count (if any) */}
        {session.errors_count > 0 && (
          <Box>
            <Typography variant="caption" color="text.secondary" display="block">
              Errors
            </Typography>
            <Typography variant="body2" color="error.main" sx={{ mt: 0.5 }}>
              {session.errors_count} error{session.errors_count > 1 ? 's' : ''}
            </Typography>
          </Box>
        )}
      </Box>

      {/* Real-time Indicator for Active Sessions */}
      {isActive && (
        <Box sx={{ 
          mt: 2, 
          pt: 2, 
          borderTop: 1, 
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}>
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
          <Typography variant="caption" color="success.main" sx={{ fontWeight: 500 }}>
            Live updates enabled - Timeline will update in real-time
          </Typography>
        </Box>
      )}
    </Paper>
  );
}

export default SessionHeader; 