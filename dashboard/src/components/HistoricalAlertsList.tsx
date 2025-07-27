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
import { Refresh, SearchOff } from '@mui/icons-material';
import AlertListItem from './AlertListItem';
import { hasActiveFilters } from '../utils/search';
import type { HistoricalAlertsListProps } from '../types';

/**
 * HistoricalAlertsList component displays completed and failed alerts
 * in a table format, enhanced for Phase 4 with filtering and search support
 */
const HistoricalAlertsList: React.FC<HistoricalAlertsListProps> = ({
  sessions = [],
  loading = false,
  error = null,
  onRefresh,
  onSessionClick,
  // Phase 4: Filter props
  filters,
  filteredCount,
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
          {/* Phase 4: Show filtered count */}
          {filteredCount !== undefined && (
            <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
              ({filteredCount.toLocaleString()} result{filteredCount !== 1 ? 's' : ''})
            </Typography>
          )}
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

      {/* Phase 4: Filter info message */}
      {filters && filters.search && filters.search.trim() && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Showing results for "{filters.search}"
          {filters.status && filters.status.length > 0 && (
            <> with status: {filters.status.join(', ')}</>
          )}
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
                      <Box sx={{ py: 6, textAlign: 'center' }}>
                        {/* Phase 4: Different empty states for filtered vs unfiltered */}
                        {filters && hasActiveFilters(filters) ? (
                          <>
                            <SearchOff sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                            <Typography variant="h6" color="text.secondary" gutterBottom>
                              No alerts found
                            </Typography>
                            <Typography variant="body2" color="text.disabled">
                              Try adjusting your search terms or filters
                            </Typography>
                          </>
                        ) : (
                          <>
                            <Typography variant="h6" color="text.secondary" gutterBottom>
                              No Historical Alerts
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              No completed or failed alerts found.
                            </Typography>
                          </>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ) : (
                  sessions.map((session) => (
                    <AlertListItem
                      key={session.session_id || `session-${Math.random()}`}
                      session={session}
                      onClick={handleSessionClick}
                      searchTerm={filters?.search}
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