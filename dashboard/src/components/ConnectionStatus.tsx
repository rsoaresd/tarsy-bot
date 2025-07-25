import React from 'react';
import { Box, Typography, Chip, Tooltip, Button } from '@mui/material';
import { WifiTethering, WifiOff, Sync, Error as ErrorIcon } from '@mui/icons-material';

interface ConnectionStatusProps {
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  errorMessage?: string | null;
  onRetry?: () => void;
}

const statusConfig = {
  connected: {
    label: 'Connected',
    color: 'success',
    icon: <WifiTethering fontSize="small" />,
  },
  connecting: {
    label: 'Connecting...',
    color: 'info',
    icon: <Sync fontSize="small" />,
  },
  disconnected: {
    label: 'Disconnected',
    color: 'warning',
    icon: <WifiOff fontSize="small" />,
  },
  error: {
    label: 'Connection Error',
    color: 'error',
    icon: <ErrorIcon fontSize="small" />,
  },
};

function ConnectionStatus({ status, errorMessage, onRetry }: ConnectionStatusProps) {
  const config = statusConfig[status] || statusConfig.error;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1 }}>
      <Tooltip title={config.label} arrow>
        <Chip
          icon={config.icon}
          label={config.label}
          color={config.color as any}
          sx={{ fontWeight: 600, fontSize: '0.95rem', height: 32 }}
          aria-label={`Connection status: ${config.label}`}
        />
      </Tooltip>
      {status === 'error' && errorMessage && (
        <Typography variant="body2" color="error" sx={{ ml: 1 }}>
          {errorMessage}
        </Typography>
      )}
      {status === 'error' && onRetry && (
        <Button variant="outlined" color="error" size="small" onClick={onRetry} sx={{ ml: 2 }}>
          Retry
        </Button>
      )}
    </Box>
  );
}

export default ConnectionStatus; 