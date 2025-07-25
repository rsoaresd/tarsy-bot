import React, { useState, useCallback, useMemo } from 'react';
import {
  Box,
  Typography,
  Chip,
  TextField,
  MenuItem,
  FormControl,
  Select,
  InputLabel,
  InputAdornment,
  Badge,
  useTheme,
} from '@mui/material';
import {
  Search as SearchIcon,
  Error as ErrorIcon,
  Warning as TimeoutIcon,
  CheckCircle as SuccessIcon,
} from '@mui/icons-material';
import { SessionFilter } from '../types';

interface FilterPanelProps {
  filters: SessionFilter;
  onFiltersChange: (filters: SessionFilter) => void;
  statusCounts?: {
    failed: number;
    timeout: number;
    success: number;
    total: number;
  };
  availableAgentTypes?: string[];
}

interface QuickFilter {
  key: string;
  label: string;
  icon: React.ReactElement;
  color: 'error' | 'warning' | 'success';
  statuses: string[];
  count: number;
}

function FilterPanel({ 
  filters, 
  onFiltersChange, 
  statusCounts = { failed: 0, timeout: 0, success: 0, total: 0 },
  availableAgentTypes = []
}: FilterPanelProps) {
  const theme = useTheme();
  const [searchValue, setSearchValue] = useState(filters.search_query || '');

  // Quick filter definitions
  const quickFilters: QuickFilter[] = useMemo(() => [
    {
      key: 'failed',
      label: 'Failed',
      icon: <ErrorIcon sx={{ fontSize: 16 }} />,
      color: 'error',
      statuses: ['error', 'failed'],
      count: statusCounts.failed,
    },
    {
      key: 'timeout',
      label: 'Timeout',
      icon: <TimeoutIcon sx={{ fontSize: 16 }} />,
      color: 'warning',
      statuses: ['timeout'],
      count: statusCounts.timeout,
    },
    {
      key: 'success',
      label: 'Success',
      icon: <SuccessIcon sx={{ fontSize: 16 }} />,
      color: 'success',
      statuses: ['completed', 'success'],
      count: statusCounts.success,
    },
  ], [statusCounts]);

  // Time filter options
  const timeFilters = [
    { key: '1h', label: '1h', hours: 1 },
    { key: '4h', label: '4h', hours: 4 },
    { key: 'today', label: 'Today', hours: 24 },
    { key: 'week', label: 'Week', hours: 168 },
  ];

  // Handle quick filter toggle
  const handleQuickFilterToggle = useCallback((quickFilter: QuickFilter) => {
    const currentStatuses = filters.status || [];
    const isActive = quickFilter.statuses.every(status => currentStatuses.includes(status));
    
    let newStatuses: string[];
    if (isActive) {
      // Remove these statuses
      newStatuses = currentStatuses.filter(status => !quickFilter.statuses.includes(status));
    } else {
      // Add these statuses
      newStatuses = Array.from(new Set([...currentStatuses, ...quickFilter.statuses]));
    }
    
    onFiltersChange({
      ...filters,
      status: newStatuses.length > 0 ? newStatuses : undefined,
    });
  }, [filters, onFiltersChange]);

  // Handle time filter
  const handleTimeFilterToggle = useCallback((timeFilter: typeof timeFilters[0]) => {
    const now = new Date();
    const startTime = new Date(now.getTime() - (timeFilter.hours * 60 * 60 * 1000));
    
    const isActive = filters.date_range?.start === startTime.toISOString();
    
    onFiltersChange({
      ...filters,
      date_range: isActive ? undefined : {
        start: startTime.toISOString(),
        end: now.toISOString(),
      },
    });
  }, [filters, onFiltersChange]);

  // Handle agent type change
  const handleAgentTypeChange = useCallback((agentTypes: string[]) => {
    onFiltersChange({
      ...filters,
      agent_type: agentTypes.length > 0 ? agentTypes : undefined,
    });
  }, [filters, onFiltersChange]);

  // Handle search with debouncing
  const handleSearchChange = useCallback((value: string) => {
    setSearchValue(value);
    
    // Debounce search updates
    const timeoutId = setTimeout(() => {
      onFiltersChange({
        ...filters,
        search_query: value.trim() || undefined,
      });
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [filters, onFiltersChange]);

  // Check if a quick filter is active
  const isQuickFilterActive = useCallback((quickFilter: QuickFilter) => {
    const currentStatuses = filters.status || [];
    return quickFilter.statuses.every(status => currentStatuses.includes(status));
  }, [filters.status]);

  // Check if a time filter is active
  const isTimeFilterActive = useCallback((timeFilter: typeof timeFilters[0]) => {
    if (!filters.date_range) return false;
    const now = new Date();
    const startTime = new Date(now.getTime() - (timeFilter.hours * 60 * 60 * 1000));
    return filters.date_range.start === startTime.toISOString();
  }, [filters.date_range]);

  return (
    <Box sx={{ mb: 3 }}>
      {/* Quick Status Filters */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <Typography variant="body2" color="text.secondary" sx={{ minWidth: 'fit-content' }}>
          Quick Filters:
        </Typography>
        
        {quickFilters.map((quickFilter) => {
          const isActive = isQuickFilterActive(quickFilter);
          
          return (
            <Chip
              key={quickFilter.key}
              icon={quickFilter.icon}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <span>{quickFilter.label}</span>
                  {quickFilter.count > 0 && (
                    <Badge
                      badgeContent={quickFilter.count}
                      color={quickFilter.color}
                      sx={{
                        '& .MuiBadge-badge': {
                          fontSize: '0.65rem',
                          minWidth: 16,
                          height: 16,
                        },
                      }}
                    >
                      <Box sx={{ width: 4 }} />
                    </Badge>
                  )}
                </Box>
              }
              onClick={() => handleQuickFilterToggle(quickFilter)}
              color={quickFilter.color}
              variant={isActive ? 'filled' : 'outlined'}
              clickable
              size="small"
              sx={{
                transition: 'all 0.2s ease-in-out',
                '&:hover': {
                  transform: 'scale(1.05)',
                },
              }}
            />
          );
        })}
      </Box>

      {/* Time Filters and Search */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: 2, 
        flexWrap: 'wrap',
        justifyContent: 'space-between',
      }}>
        {/* Time Filter Section */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Typography variant="body2" color="text.secondary">
            Time:
          </Typography>
          
          {timeFilters.map((timeFilter) => {
            const isActive = isTimeFilterActive(timeFilter);
            
            return (
              <Chip
                key={timeFilter.key}
                label={timeFilter.label}
                onClick={() => handleTimeFilterToggle(timeFilter)}
                variant={isActive ? 'filled' : 'outlined'}
                color={isActive ? 'primary' : 'default'}
                size="small"
                clickable
                sx={{
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'scale(1.05)',
                  },
                }}
              />
            );
          })}
        </Box>

        {/* Agent Type Filter and Search */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, minWidth: 300 }}>
          {/* Agent Type Dropdown */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Agent Type</InputLabel>
            <Select
              multiple
              value={filters.agent_type || []}
              onChange={(e) => handleAgentTypeChange(e.target.value as string[])}
              label="Agent Type"
              renderValue={(selected) => 
                selected.length === 0 ? 'All Agents' : `${selected.length} selected`
              }
            >
              {availableAgentTypes.map((agentType) => (
                <MenuItem key={agentType} value={agentType}>
                  {agentType}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Search Field */}
          <TextField
            size="small"
            placeholder="Search sessions..."
            value={searchValue}
            onChange={(e) => handleSearchChange(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ minWidth: 200 }}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Active Filters Summary */}
      {(filters.status?.length || filters.agent_type?.length || filters.search_query || filters.date_range) && (
        <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
          <Typography variant="caption" color="text.secondary">
            Active filters: 
            {filters.status?.length && ` Status (${filters.status.length})`}
            {filters.agent_type?.length && ` • Agent (${filters.agent_type.length})`}
            {filters.search_query && ' • Search'}
            {filters.date_range && ' • Time Range'}
          </Typography>
        </Box>
      )}
    </Box>
  );
}

export default FilterPanel; 