import React, { useState, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  Button,
  IconButton,
  LinearProgress,
  Collapse,
  Divider,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Error as ErrorIcon,
  PlayArrow as ProcessingIcon,
  CheckCircle as CompletingIcon,
  Visibility as ViewIcon,
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { AlertStatus } from '../types';

interface ActiveAlertsPanelProps {
  activeAlerts: AlertStatus[];
  onRefresh?: () => void;
}

interface StatusCounts {
  processing: number;
  failed: number;
  pending: number;
  completing: number;
}

function ActiveAlertsPanel({ activeAlerts, onRefresh }: ActiveAlertsPanelProps) {
  const theme = useTheme();
  const navigate = useNavigate();
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // Calculate status counts
  const statusCounts = activeAlerts.reduce<StatusCounts>((counts, alert) => {
    switch (alert.status) {
      case 'processing':
        counts.processing++;
        break;
      case 'failed':
        counts.failed++;
        break;
      case 'pending':
        counts.pending++;
        break;
      case 'completed':
        counts.completing++;
        break;
    }
    return counts;
  }, { processing: 0, failed: 0, pending: 0, completing: 0 });

  const toggleExpanded = useCallback((alertId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(alertId)) {
        newSet.delete(alertId);
      } else {
        newSet.add(alertId);
      }
      return newSet;
    });
  }, []);

  const handleViewDetails = useCallback((alert: AlertStatus) => {
    if (alert.session_id) {
      navigate(`/sessions/${alert.session_id}`);
    }
  }, [navigate]);

  const handleCopyError = useCallback(async (error: string) => {
    try {
      await navigator.clipboard.writeText(error);
      // Could show a snackbar notification here
    } catch (err) {
      console.error('Failed to copy error:', err);
    }
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'failed':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'processing':
        return <ProcessingIcon sx={{ color: 'warning.main' }} />;
      case 'completed':
        return <CompletingIcon sx={{ color: 'success.main' }} />;
      default:
        return <ProcessingIcon sx={{ color: 'grey.500' }} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'failed':
        return 'error.main';
      case 'processing':
        return 'warning.main';
      case 'completed':
        return 'success.main';
      default:
        return 'grey.500';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'failed':
        return 'FAILED';
      case 'processing':
        return 'PROCESSING';
      case 'completed':
        return 'COMPLETING';
      case 'pending':
        return 'PENDING';
      default:
        return status.toUpperCase();
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (activeAlerts.length === 0) {
    return (
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h2" gutterBottom>
          🟢 No Active Alerts
        </Typography>
        <Typography variant="body1" color="text.secondary">
          All alerts are currently resolved. The system is operating normally.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      {/* Header with Status Counters */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h2" component="h2">
          ACTIVE ALERTS
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={`${statusCounts.processing} Processing`}
            color="warning"
            variant={statusCounts.processing > 0 ? 'filled' : 'outlined'}
            size="small"
          />
          <Chip
            label={`${statusCounts.failed} Failed`}
            color="error"
            variant={statusCounts.failed > 0 ? 'filled' : 'outlined'}
            size="small"
          />
          <Chip
            label={`${statusCounts.pending} Pending`}
            color="default"
            variant={statusCounts.pending > 0 ? 'filled' : 'outlined'}
            size="small"
          />
        </Box>
      </Box>

      {/* Active Alert Cards */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {activeAlerts.map((alert) => {
          const isExpanded = expandedCards.has(alert.alert_id);
          const statusColor = getStatusColor(alert.status);
          
          return (
            <Card
              key={alert.alert_id}
              sx={{
                borderLeft: `4px solid ${theme.palette.mode === 'light' ? statusColor : statusColor}`,
                transition: 'all 0.2s ease-in-out',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 2,
                  transform: 'translateY(-1px)',
                },
              }}
              onClick={() => toggleExpanded(alert.alert_id)}
            >
              <CardContent sx={{ pb: isExpanded ? 1 : 2 }}>
                {/* Alert Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getStatusIcon(alert.status)}
                    
                    <Typography
                      variant="body1"
                      sx={{ color: statusColor, fontWeight: 600 }}
                    >
                      {getStatusLabel(alert.status)}
                    </Typography>
                    
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {alert.current_agent || 'Unknown Agent'}
                    </Typography>
                    
                    <Typography variant="body1">
                      {alert.current_step}
                    </Typography>
                    
                    <Typography variant="caption" color="text.secondary">
                      {formatDuration(Math.floor(Date.now() / 1000) - new Date().getTime() / 1000)}
                    </Typography>
                  </Box>
                  
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleExpanded(alert.alert_id);
                    }}
                    aria-label={isExpanded ? 'Collapse alert details' : 'Expand alert details'}
                  >
                    {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>

                {/* Progress Bar for Processing Alerts */}
                {alert.status === 'processing' && (
                  <Box sx={{ mt: 1, mb: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" color="text.secondary">
                        Progress: {alert.progress}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ETA: Calculating...
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={alert.progress}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: 'grey.200',
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 3,
                          backgroundColor: statusColor,
                        },
                      }}
                    />
                  </Box>
                )}

                {/* Expanded Content */}
                <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {/* Status Details */}
                    {alert.status === 'failed' && alert.error && (
                      <Box>
                        <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          ❌ Processing Failed
                          <Typography variant="body2" color="error.main">
                            {alert.error}
                          </Typography>
                        </Typography>
                      </Box>
                    )}
                    
                    {alert.status === 'processing' && (
                      <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        🔄 In Progress
                        <Typography variant="body2" color="warning.main">
                          {alert.current_step}
                        </Typography>
                      </Typography>
                    )}
                    
                    {alert.status === 'completed' && alert.result && (
                      <Box>
                        <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          ✅ Analysis Complete
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          Resolution: {alert.result}
                        </Typography>
                      </Box>
                    )}

                    {/* MCP Servers */}
                    {alert.assigned_mcp_servers && alert.assigned_mcp_servers.length > 0 && (
                      <Typography variant="body2" color="text.secondary">
                        MCP Servers: {alert.assigned_mcp_servers.join(', ')}
                      </Typography>
                    )}

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 1 }}>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewDetails(alert);
                        }}
                        aria-label={`View details for ${alert.current_step}`}
                      >
                        {alert.status === 'processing' ? 'Watch' : 'View Details'}
                      </Button>
                      
                      {alert.error && (
                        <Button
                          size="small"
                          startIcon={<CopyIcon />}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleCopyError(alert.error!);
                          }}
                          aria-label="Copy error details"
                        >
                          Copy Error
                        </Button>
                      )}
                    </Box>
                  </Box>
                </Collapse>
              </CardContent>
            </Card>
          );
        })}
      </Box>
    </Paper>
  );
}

export default ActiveAlertsPanel; 