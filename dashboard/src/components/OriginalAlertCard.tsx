import { Paper, Typography, Box, Chip } from '@mui/material';
import type { OriginalAlertCardProps } from '../types';
import { formatTimestamp } from '../utils/timestamp';

/**
 * Get severity color for alert severity levels
 */
const getSeverityColor = (severity: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (severity.toLowerCase()) {
    case 'critical':
      return 'error';
    case 'high':
      return 'warning';
    case 'medium':
      return 'info';
    case 'low':
      return 'success';
    default:
      return 'default';
  }
};

/**
 * Get environment color for different environments
 */
const getEnvironmentColor = (environment: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
  switch (environment.toLowerCase()) {
    case 'production':
      return 'error';
    case 'staging':
      return 'warning';
    case 'development':
      return 'info';
    default:
      return 'default';
  }
};

/**
 * OriginalAlertCard component - Phase 3
 * Displays structured original alert data with severity indicators and environment information
 */
function OriginalAlertCard({ alertData }: OriginalAlertCardProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
        Original Alert Data
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {/* Alert Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
          <Chip 
            label={alertData.severity.toUpperCase()} 
            color={getSeverityColor(alertData.severity)} 
            size="small"
            sx={{ fontWeight: 600 }}
          />
          <Chip 
            label={alertData.environment.toUpperCase()} 
            color={getEnvironmentColor(alertData.environment)} 
            size="small"
            variant="outlined"
          />
          <Typography variant="body2" color="text.secondary">
            {alertData.alert_type}
          </Typography>
        </Box>

        {/* Alert Message */}
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Message
          </Typography>
          <Typography variant="body1" sx={{ 
            backgroundColor: 'grey.50', 
            p: 2, 
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.875rem',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            overflowWrap: 'break-word'
          }}>
            {alertData.message}
          </Typography>
        </Box>

        {/* Metadata */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Metadata
          </Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 1 }}>
            <Typography variant="body2">
              <strong>Timestamp:</strong> {formatTimestamp(alertData.timestamp_us, 'absolute')}
            </Typography>
            <Typography variant="body2">
              <strong>Cluster:</strong> {alertData.cluster}
            </Typography>
            <Typography variant="body2">
              <strong>Namespace:</strong> {alertData.namespace}
            </Typography>
            {alertData.pod && (
              <Typography variant="body2">
                <strong>Pod:</strong> {alertData.pod}
              </Typography>
            )}
          </Box>
        </Box>

        {/* Context and Runbook */}
        {(alertData.context || alertData.runbook) && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {alertData.context && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Context
                </Typography>
                <Typography variant="body2" sx={{ 
                  backgroundColor: 'grey.50', 
                  p: 1.5, 
                  borderRadius: 1,
                  fontSize: '0.825rem',
                  whiteSpace: 'pre-wrap'
                }}>
                  {alertData.context}
                </Typography>
              </Box>
            )}
            
            {alertData.runbook && (
              <Box>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Runbook Reference
                </Typography>
                <Typography variant="body2" sx={{ 
                  backgroundColor: 'info.50', 
                  color: 'info.main',
                  p: 1.5, 
                  borderRadius: 1,
                  fontSize: '0.825rem',
                  fontFamily: 'monospace'
                }}>
                  {alertData.runbook}
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default OriginalAlertCard; 