import React from 'react';
import { TableRow, TableCell, Typography } from '@mui/material';
import StatusBadge from './StatusBadge';
import type { AlertListItemProps } from '../types';

// Format duration helper function
const formatDuration = (durationMs: number | null): string => {
  if (!durationMs) return '-';
  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
  const minutes = Math.floor(durationMs / 60000);
  const seconds = Math.floor((durationMs % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
};

// Format time helper function
const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

/**
 * AlertListItem component represents a single session row in the alerts table
 * Displays basic session information: status, type, agent, time, and duration
 */
const AlertListItem: React.FC<AlertListItemProps> = ({ session, onClick }) => {
  const handleRowClick = () => {
    if (onClick) {
      if (!session.session_id) {
        console.warn('Session has no ID:', session);
        return;
      }
      onClick(session.session_id);
    }
  };

  return (
    <TableRow 
      hover 
      onClick={handleRowClick}
      sx={{ 
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': {
          backgroundColor: 'action.hover',
        },
      }}
    >
      <TableCell>
        <StatusBadge status={session.status} />
      </TableCell>
      <TableCell>
        <Typography variant="body2" sx={{ fontWeight: 500 }}>
          {session.alert_type}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {session.agent_type}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {formatTime(session.started_at)}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {formatDuration(session.duration_ms)}
        </Typography>
      </TableCell>
    </TableRow>
  );
};

export default AlertListItem; 