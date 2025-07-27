import { Paper, Typography, Box, Chip, Link } from '@mui/material';
import { AccessTime, OpenInNew } from '@mui/icons-material';
import type { OriginalAlertCardProps } from '../types';
import { formatTimestamp } from '../utils/timestamp';

/**
 * Transform cluster API URL to OpenShift console URL
 * Input: https://api.<cluster-domain>:<port>
 * Output: https://console-openshift-console.apps.<cluster-domain>/
 */
const getConsoleUrlFromCluster = (clusterUrl: string): string => {
  try {
    // Handle both with and without https:// prefix
    const urlToParse = clusterUrl.startsWith('http') ? clusterUrl : `https://${clusterUrl}`;
    const url = new URL(urlToParse);
    
    // Extract domain from api.<cluster-domain>
    const hostname = url.hostname;
    if (hostname.startsWith('api.')) {
      const clusterDomain = hostname.substring(4); // Remove 'api.' prefix
      return `https://console-openshift-console.apps.${clusterDomain}/`;
    }
    
    // Fallback: if it doesn't match expected pattern, return original
    return clusterUrl;
  } catch (error) {
    // If URL parsing fails, return original
    return clusterUrl;
  }
};

/**
 * Generate namespace/project URL for OpenShift console
 * Input: cluster URL and namespace name
 * Output: https://console-openshift-console.apps.<cluster-domain>/k8s/cluster/projects/<namespace>
 */
const getNamespaceConsoleUrl = (clusterUrl: string, namespace: string): string => {
  const consoleBaseUrl = getConsoleUrlFromCluster(clusterUrl);
  // Remove trailing slash if present and append namespace path
  const baseUrl = consoleBaseUrl.endsWith('/') ? consoleBaseUrl.slice(0, -1) : consoleBaseUrl;
  return `${baseUrl}/k8s/cluster/projects/${namespace}`;
};

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
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
          {/* Left side: Severity, Environment, Alert Type */}
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

          {/* Right side: Timestamp */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 'auto' }}>
            <AccessTime fontSize="small" sx={{ color: 'text.secondary' }} />
            <Typography variant="body2" sx={{ 
              fontFamily: 'monospace', 
              fontSize: '0.875rem',
              color: 'text.secondary'
            }}>
              {formatTimestamp(alertData.timestamp_us, 'absolute')}
            </Typography>
          </Box>
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

        {/* Infrastructure Information - Vertical Stack */}
        <Box>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Infrastructure
          </Typography>
          
          {/* Cluster - Full width for long names */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Cluster
            </Typography>
            <Link
              href={getConsoleUrlFromCluster(alertData.cluster)}
              target="_blank"
              rel="noopener noreferrer"
              sx={{ 
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                fontFamily: 'monospace', 
                fontSize: '0.875rem',
                backgroundColor: 'grey.50',
                px: 1,
                py: 0.5,
                borderRadius: 0.5,
                wordBreak: 'break-word',
                textDecoration: 'none',
                color: 'text.primary',
                '&:hover': {
                  backgroundColor: 'grey.100',
                  textDecoration: 'underline'
                }
              }}
            >
              <OpenInNew fontSize="small" sx={{ color: 'text.secondary' }} />
              {alertData.cluster}
            </Link>
          </Box>

          {/* Namespace and Pod - Same row for compact layout */}
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: alertData.pod ? '1fr 1fr' : '1fr',
            gap: 2,
            mb: 2
          }}>
            <Box>
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                Namespace
              </Typography>
              <Link
                href={getNamespaceConsoleUrl(alertData.cluster, alertData.namespace)}
                target="_blank"
                rel="noopener noreferrer"
                sx={{ 
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  fontFamily: 'monospace', 
                  fontSize: '0.875rem',
                  backgroundColor: 'grey.50',
                  px: 1,
                  py: 0.5,
                  borderRadius: 0.5,
                  textDecoration: 'none',
                  color: 'text.primary',
                  '&:hover': {
                    backgroundColor: 'grey.100',
                    textDecoration: 'underline'
                  }
                }}
              >
                <OpenInNew fontSize="small" sx={{ color: 'text.secondary' }} />
                {alertData.namespace}
              </Link>
            </Box>
            
            {alertData.pod && (
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                  Pod
                </Typography>
                <Typography variant="body2" sx={{ 
                  fontFamily: 'monospace', 
                  fontSize: '0.875rem',
                  backgroundColor: 'grey.50',
                  px: 1,
                  py: 0.5,
                  borderRadius: 0.5,
                  wordBreak: 'break-word'
                }}>
                  {alertData.pod}
                </Typography>
              </Box>
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
                <Link
                  href={alertData.runbook}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    backgroundColor: 'info.50', 
                    color: 'info.main',
                    p: 1.5, 
                    borderRadius: 1,
                    fontSize: '0.825rem',
                    fontFamily: 'monospace',
                    textDecoration: 'none',
                    '&:hover': {
                      backgroundColor: 'info.100',
                      textDecoration: 'underline'
                    }
                  }}
                >
                  <OpenInNew fontSize="small" />
                  {alertData.runbook}
                </Link>
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default OriginalAlertCard; 