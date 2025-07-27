import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  Alert,
  Box,
  Button,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import AlertListItem from './AlertListItem';
import type { HistoricalAlertsListProps } from '../types';

/**
 * HistoricalAlertsList component displays completed and failed alerts
 * in a table format similar to Phase 1, but specifically for historical data
 */
const HistoricalAlertsList: React.FC<HistoricalAlertsListProps> = ({
  sessions = [],
  loading = false,
  error = null,
  onRefresh,
  onSessionClick,
}) => {
  // Handle session row click
  const handleSessionClick = (sessionId: string) => {
    if (!sessionId) {
      console.warn('Historical session clicked but no ID provided');
      return;
    }
    console.log('Historical session clicked:', sessionId);
    
    if (onSessionClick) {
      onSessionClick(sessionId);
    }
    // Phase 3 will implement navigation to detail view
  };

  // Handle manual refresh
  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      {/* Panel Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Alert History
        </Typography>
        
        {/* Refresh Button */}
        <Button
          variant="outlined"
          size="small"
          startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </Button>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => {}}>
          {error}
        </Alert>
      )}

      {/* Loading State */}
      {loading && sessions.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Historical Alerts Table */}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Agent</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Duration</TableCell>
                  <TableCell sx={{ fontWeight: 600, width: 60, textAlign: 'center' }}></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sessions.length === 0 ? (
                  <TableRow key="empty-state">
                    <TableCell colSpan={6} align="center">
                      <Box sx={{ py: 6 }}>
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          No Historical Alerts
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          No completed or failed alerts found.
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  sessions.map((session) => (
                    <AlertListItem
                      key={session.session_id || `session-${Math.random()}`}
                      session={session}
                      onClick={handleSessionClick}
                    />
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Summary */}
          {sessions.length > 0 && (
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="body2" color="text.secondary">
                Showing {sessions.length} historical alert{sessions.length !== 1 ? 's' : ''} (completed/failed)
              </Typography>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};

export default HistoricalAlertsList; 