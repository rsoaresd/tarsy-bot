import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Button,
  IconButton,
  Pagination,
  FormControl,
  Select,
  MenuItem,
  Chip,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Visibility as ViewIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as TimeoutIcon,
  Schedule as PendingIcon,
} from '@mui/icons-material';
import { FixedSizeList as List } from 'react-window';
import { useNavigate } from 'react-router-dom';
import { SessionSummary, PaginationOptions } from '../types';

interface HistoricalSessionsListProps {
  sessions: SessionSummary[];
  pagination: PaginationOptions;
  onPaginationChange: (pagination: PaginationOptions) => void;
  isLoading?: boolean;
}

type SortDirection = 'asc' | 'desc';
type SortField = 'start_time' | 'status' | 'agent_type' | 'interactions_count' | 'progress_percentage';

interface TableRowData {
  sessions: SessionSummary[];
  onRowClick: (sessionId: string) => void;
}

function HistoricalSessionsList({ 
  sessions, 
  pagination, 
  onPaginationChange, 
  isLoading = false 
}: HistoricalSessionsListProps) {
  const theme = useTheme();
  const navigate = useNavigate();
  const [sortField, setSortField] = useState<SortField>('start_time');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Sort sessions
  const sortedSessions = useMemo(() => {
    if (!sessions.length) return [];
    
    return [...sessions].sort((a, b) => {
      let aValue: any;
      let bValue: any;
      
      switch (sortField) {
        case 'start_time':
          aValue = new Date(a.start_time || 0).getTime();
          bValue = new Date(b.start_time || 0).getTime();
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'agent_type':
          aValue = a.agent_type || '';
          bValue = b.agent_type || '';
          break;
        case 'interactions_count':
          aValue = a.interactions_count;
          bValue = b.interactions_count;
          break;
        case 'progress_percentage':
          aValue = a.progress_percentage;
          bValue = b.progress_percentage;
          break;
        default:
          return 0;
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [sessions, sortField, sortDirection]);

  // Handle sort change
  const handleSort = useCallback((field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  }, [sortField]);

  // Handle row click
  const handleRowClick = useCallback((sessionId: string) => {
    navigate(`/sessions/${sessionId}`);
  }, [navigate]);

  // Handle pagination change
  const handlePageChange = useCallback((event: React.ChangeEvent<unknown>, page: number) => {
    onPaginationChange({
      ...pagination,
      page: page,
    });
  }, [pagination, onPaginationChange]);

  // Handle page size change
  const handlePageSizeChange = useCallback((pageSize: number) => {
    onPaginationChange({
      ...pagination,
      per_page: pageSize,
      page: 1, // Reset to first page when changing page size
    });
  }, [pagination, onPaginationChange]);

  // Get status icon and color
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return {
          icon: <SuccessIcon sx={{ fontSize: 16, color: 'success.main' }} />,
          color: 'success.main',
          label: '✓',
        };
      case 'error':
      case 'failed':
        return {
          icon: <ErrorIcon sx={{ fontSize: 16, color: 'error.main' }} />,
          color: 'error.main',
          label: '✗',
        };
      case 'timeout':
        return {
          icon: <TimeoutIcon sx={{ fontSize: 16, color: 'warning.main' }} />,
          color: 'warning.main',
          label: '⚠',
        };
      default:
        return {
          icon: <PendingIcon sx={{ fontSize: 16, color: 'grey.500' }} />,
          color: 'grey.500',
          label: '○',
        };
    }
  };

  // Format duration
  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime) return '-';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const durationMs = end.getTime() - start.getTime();
    const durationSeconds = Math.floor(durationMs / 1000);
    
    if (durationSeconds < 60) return `${durationSeconds}s`;
    if (durationSeconds < 3600) return `${Math.floor(durationSeconds / 60)}m`;
    return `${Math.floor(durationSeconds / 3600)}h`;
  };

  // Format time
  const formatTime = (timestamp?: string) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Calculate total pages
  const totalPages = Math.ceil(pagination.total / pagination.per_page);

  if (sessions.length === 0 && !isLoading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h2" gutterBottom>
          No Historical Sessions Found
        </Typography>
        <Typography variant="body1" color="text.secondary">
          No sessions match the current filter criteria. Try adjusting your filters or check back later.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h2" component="h2">
          ALERT HISTORY
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          {pagination.total.toLocaleString()} sessions total
        </Typography>
      </Box>

      {/* Table */}
      <TableContainer sx={{ maxHeight: 600, mb: 2 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, minWidth: 80 }}>
                <TableSortLabel
                  active={sortField === 'status'}
                  direction={sortField === 'status' ? sortDirection : 'asc'}
                  onClick={() => handleSort('status')}
                >
                  Status
                </TableSortLabel>
              </TableCell>
              
              <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>
                <TableSortLabel
                  active={sortField === 'agent_type'}
                  direction={sortField === 'agent_type' ? sortDirection : 'asc'}
                  onClick={() => handleSort('agent_type')}
                >
                  Agent
                </TableSortLabel>
              </TableCell>
              
              <TableCell sx={{ fontWeight: 600, minWidth: 200 }}>
                Alert Type
              </TableCell>
              
              <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>
                <TableSortLabel
                  active={sortField === 'start_time'}
                  direction={sortField === 'start_time' ? sortDirection : 'asc'}
                  onClick={() => handleSort('start_time')}
                >
                  Time
                </TableSortLabel>
              </TableCell>
              
              <TableCell sx={{ fontWeight: 600, minWidth: 80 }}>
                Duration
              </TableCell>
              
              <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>
                Actions
              </TableCell>
            </TableRow>
          </TableHead>
          
          <TableBody>
            {isLoading ? (
              // Loading skeleton rows
              [...Array(pagination.per_page)].map((_, index) => (
                <TableRow key={`loading-${index}`}>
                  <TableCell colSpan={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, py: 1 }}>
                      <Box sx={{ width: 20, height: 20, bgcolor: 'grey.200', borderRadius: '50%' }} />
                      <Box sx={{ width: 60, height: 16, bgcolor: 'grey.200', borderRadius: 1 }} />
                      <Box sx={{ width: 120, height: 16, bgcolor: 'grey.200', borderRadius: 1 }} />
                      <Box sx={{ width: 80, height: 16, bgcolor: 'grey.200', borderRadius: 1 }} />
                      <Box sx={{ width: 60, height: 16, bgcolor: 'grey.200', borderRadius: 1 }} />
                      <Box sx={{ width: 100, height: 32, bgcolor: 'grey.200', borderRadius: 1 }} />
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              sortedSessions.map((session) => {
                const statusDisplay = getStatusDisplay(session.status);
                
                return (
                  <TableRow
                    key={session.session_id}
                    hover
                    sx={{
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => handleRowClick(session.session_id)}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Tooltip title={session.status} arrow>
                          <Box>{statusDisplay.icon}</Box>
                        </Tooltip>
                        <Typography variant="body2" sx={{ color: statusDisplay.color }}>
                          {statusDisplay.label}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Chip
                        label={session.agent_type || 'Unknown'}
                        size="small"
                        variant="outlined"
                        sx={{ fontSize: '0.75rem' }}
                      />
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap>
                        {session.current_step || 'No description'}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatTime(session.start_time)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {formatDuration(session.start_time, session.last_activity)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Button
                        size="small"
                        startIcon={<ViewIcon />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRowClick(session.session_id);
                        }}
                        aria-label={`View details for session ${session.session_id}`}
                      >
                        Details
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Controls */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 2,
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Show:
          </Typography>
          <FormControl size="small" sx={{ minWidth: 80 }}>
            <Select
              value={pagination.per_page}
              onChange={(e) => handlePageSizeChange(e.target.value as number)}
              variant="outlined"
            >
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={25}>25</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
          <Typography variant="body2" color="text.secondary">
            per page
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {((pagination.page - 1) * pagination.per_page) + 1}-{Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total.toLocaleString()}
          </Typography>
          
          <Pagination
            count={totalPages}
            page={pagination.page}
            onChange={handlePageChange}
            color="primary"
            size="small"
            showFirstButton
            showLastButton
            siblingCount={1}
            boundaryCount={1}
          />
        </Box>
      </Box>
    </Paper>
  );
}

export default HistoricalSessionsList; 