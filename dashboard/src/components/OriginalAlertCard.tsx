import { Paper, Typography, Card, CardContent, Stack, Box, Chip, Link } from '@mui/material';
import { Warning, Info, OpenInNew } from '@mui/icons-material';
import type { OriginalAlertCardProps } from '../types';

/**
 * Get severity color for chip display
 */
const getSeverityColor = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'error';
    case 'high':
      return 'error';
    case 'medium':
      return 'warning';
    case 'low':
      return 'info';
    default:
      return 'info';
  }
};

/**
 * Get environment color for chip display
 */
const getEnvironmentColor = (environment: string): 'error' | 'warning' | 'info' => {
  switch (environment.toLowerCase()) {
    case 'production':
      return 'error';
    case 'staging':
      return 'warning';
    case 'development':
      return 'info';
    default:
      return 'info';
  }
};

/**
 * Format timestamp for display
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
 * OriginalAlertCard component - Phase 3
 * Displays structured original alert data with severity indicators and environment information
 */
function OriginalAlertCard({ alertData }: OriginalAlertCardProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Warning color="warning" />
        Original Alert Information
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Primary and Environment Info */}
        <Box sx={{ display: 'flex', gap: 3, flexDirection: { xs: 'column', md: 'row' } }}>
          {/* Primary Alert Info */}
          <Box sx={{ flex: 1 }}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                  Alert Details
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Alert Type
                    </Typography>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {alertData.alert_type}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Severity
                    </Typography>
                    <Chip 
                      label={alertData.severity} 
                      color={getSeverityColor(alertData.severity)}
                      size="small"
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Message
                    </Typography>
                    <Typography variant="body1">
                      {alertData.message}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Timestamp
                    </Typography>
                    <Typography variant="body1">
                      {formatTimestamp(alertData.timestamp)}
                    </Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Box>

          {/* Environment & Infrastructure */}
          <Box sx={{ flex: 1 }}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                  Environment & Infrastructure
                </Typography>
                <Stack spacing={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Environment
                    </Typography>
                    <Chip 
                      label={alertData.environment} 
                      color={getEnvironmentColor(alertData.environment)}
                      size="small"
                      icon={alertData.environment === 'production' ? <Warning /> : <Info />}
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Cluster
                    </Typography>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {alertData.cluster}
                    </Typography>
                  </Box>
                  
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Namespace
                    </Typography>
                    <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {alertData.namespace}
                    </Typography>
                  </Box>
                  
                  {alertData.pod && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Pod
                      </Typography>
                      <Typography variant="body1" sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                        {alertData.pod}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Box>
        </Box>

        {/* Additional Context & Runbook */}
        {(alertData.context || alertData.runbook) && (
          <Box>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                  Additional Information
                </Typography>
                <Stack spacing={2}>
                  {alertData.runbook && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Runbook
                      </Typography>
                      <Link 
                        href={alertData.runbook} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                      >
                        <OpenInNew fontSize="small" />
                        {alertData.runbook}
                      </Link>
                    </Box>
                  )}
                  
                  {alertData.context && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Context
                      </Typography>
                      <Typography variant="body1">
                        {alertData.context}
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default OriginalAlertCard; 