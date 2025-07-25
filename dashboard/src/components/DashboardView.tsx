import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Box, CircularProgress, Alert, Snackbar, Paper, Typography, Chip } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { useDashboardUpdates, useWebSocketCleanup } from '../hooks/useWebSocket';
import { 
  useCachedSessionList, 
  useCachedDashboardMetrics, 
  useCachedActiveSessions,
  usePerformanceMonitoring,
  useCacheStats,
} from '../hooks/useSessionCache';
import { dashboardApi, formatApiError } from '../services/api';
import RealTimeMonitor from './RealTimeMonitor';
import ActiveAlertsPanel from './ActiveAlertsPanel';
import FilterPanel from './FilterPanel';
import VirtualizedSessionGrid from './VirtualizedSessionGrid';
import {
  DashboardState,
  SessionFilter,
  PaginationOptions,
  AlertStatus,
  SessionSummary,
  DashboardMetrics,
} from '../types';

function DashboardView() {
  const navigate = useNavigate();
  
  // Performance monitoring
  const { metrics: perfMetrics, startMeasure, endMeasure } = usePerformanceMonitoring();
  const cacheStats = useCacheStats();

  // State management
  const [filters, setFilters] = useState<SessionFilter>({});
  const [pagination, setPagination] = useState<PaginationOptions>({
    page: 1,
    per_page: 50, // Increased for virtual scrolling
    total: 0,
  });

  const [error, setError] = useState<string | null>(null);
  const [availableAgentTypes, setAvailableAgentTypes] = useState<string[]>([]);

  // Cached data hooks for optimal performance
  const { 
    metrics: dashboardMetrics, 
    loading: metricsLoading, 
    reload: reloadMetrics 
  } = useCachedDashboardMetrics();

  const { 
    sessions: activeSessions, 
    loading: activeLoading, 
    reload: reloadActiveSessions 
  } = useCachedActiveSessions();

  const { 
    sessions: historicalSessions, 
    loading: sessionsLoading, 
    hasNextPage, 
    loadMore,
    reload: reloadSessions 
  } = useCachedSessionList(filters, { page: pagination.page, page_size: pagination.per_page });

  // WebSocket integration for real-time updates
  const { isSubscribed, updates, error: wsError } = useDashboardUpdates(
    useCallback((updateData: any) => {
      // Real-time updates handled by cached hooks
      if (updateData.active_alerts_changed) {
        reloadActiveSessions();
      }
      if (updateData.metrics_changed) {
        reloadMetrics();
      }
      if (updateData.sessions_changed) {
        reloadSessions();
      }
    }, [reloadActiveSessions, reloadMetrics, reloadSessions])
  );

  // Cleanup WebSocket on unmount
  useWebSocketCleanup();

  // Performance measurement
  useEffect(() => {
    startMeasure();
    return () => {
      endMeasure();
    };
  });

  // Computed values (memoized for performance)
  const statusCounts = useMemo(() => {
    return historicalSessions.reduce((counts, session) => {
      switch (session.status) {
        case 'error':
          counts.failed++;
          break;
        case 'completed':
          counts.completed++;
          counts.success++;
          break;
        case 'active':
          counts.active++;
          break;
        case 'timeout':
          counts.timeout++;
          break;
        default:
          break;
      }
      counts.total++;
      return counts;
    }, { active: 0, completed: 0, failed: 0, timeout: 0, success: 0, total: 0 });
  }, [historicalSessions]);

  // Convert active sessions to alert format (memoized)
  const activeAlerts: AlertStatus[] = useMemo(() => {
    return activeSessions.map(session => ({
      alert_id: session.session_id,
      status: session.status === 'active' ? 'processing' : session.status as AlertStatus['status'],
      progress: session.progress_percentage || 0,
      current_step: session.current_step || 'Starting...',
      current_agent: session.agent_type,
      session_id: session.session_id,
      error: session.errors_count > 0 ? 'Processing errors detected' : undefined,
    }));
  }, [activeSessions]);

  // Dashboard state (memoized)
  const dashboardState: DashboardState = useMemo(() => ({
    activeAlerts,
    historicalSessions,
    metrics: dashboardMetrics || {
      active_sessions: 0,
      completed_sessions: 0,
      failed_sessions: 0,
      total_interactions: 0,
      avg_session_duration: 0,
      error_rate: 0,
      last_updated: new Date().toISOString(),
    },
    isConnected: isSubscribed,
    connectionStatus: isSubscribed ? 'connected' : 'disconnected',
    lastUpdate: new Date().toISOString(),
  }), [activeAlerts, historicalSessions, dashboardMetrics, isSubscribed]);

  // Load available agent types
  const loadAgentTypes = useCallback(async () => {
    try {
      const types = await dashboardApi.getFilterOptions();
      setAvailableAgentTypes(types.agent_types || []);
    } catch (err) {
      console.warn('Failed to load agent types:', err);
      // Non-critical, continue without agent types
    }
  }, []);

  // Event handlers
  const handleRefresh = useCallback(async () => {
    await Promise.all([
      reloadMetrics(),
      reloadActiveSessions(),
      reloadSessions(),
    ]);
  }, [reloadMetrics, reloadActiveSessions, reloadSessions]);

  const handleFiltersChange = useCallback((newFilters: SessionFilter) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  }, []);

  const handlePaginationChange = useCallback((newPagination: Partial<PaginationOptions>) => {
    setPagination(prev => ({ ...prev, ...newPagination }));
  }, []);

  const handleSessionClick = useCallback((session: SessionSummary) => {
    navigate(`/sessions/${session.session_id}`);
  }, [navigate]);

  // Load agent types on mount
  useEffect(() => {
    loadAgentTypes();
  }, [loadAgentTypes]);

  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      setError(`WebSocket error: ${wsError}`);
    }
  }, [wsError]);

  // Update pagination total when historical sessions change
  useEffect(() => {
    if (historicalSessions.length > 0) {
      setPagination(prev => ({
        ...prev,
        total: historicalSessions.length,
      }));
    }
  }, [historicalSessions.length]);

  const isLoading = metricsLoading || activeLoading || sessionsLoading;
  const isRefreshing = isLoading;

  if (error) {
    return (
      <Box>
        <RealTimeMonitor
          statusCounts={statusCounts}
          lastUpdate={updates ? new Date() : undefined}
          autoRefreshEnabled={isSubscribed}
        />
        
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          action={
            <button onClick={handleRefresh}>
              Retry
            </button>
          }
        >
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Real-time Monitor Header with Performance Stats */}
      <RealTimeMonitor
        statusCounts={statusCounts}
        lastUpdate={updates ? new Date() : undefined}
        autoRefreshEnabled={isSubscribed}
      />

      {/* Performance Stats Panel (Development Only) */}
      {process.env.NODE_ENV === 'development' && (
        <Paper sx={{ p: 2, mb: 2, backgroundColor: 'rgba(0, 0, 0, 0.05)' }}>
          <Typography variant="h3" gutterBottom>
            Performance Metrics
          </Typography>
          
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Render Performance
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`${perfMetrics.renderCount} renders`} size="small" />
                <Chip label={`${perfMetrics.avgRenderTime}ms avg`} size="small" />
              </Box>
            </Box>
            
            <Box>
              <Typography variant="caption" color="text.secondary">
                Cache Performance
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip label={`${cacheStats.hitRate}% hit rate`} size="small" />
                <Chip label={`${cacheStats.size} entries`} size="small" />
                <Chip label={`${cacheStats.memoryUsage}KB`} size="small" />
              </Box>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Active Alerts Panel - Top Section */}
      <ActiveAlertsPanel
        activeAlerts={dashboardState.activeAlerts}
        onRefresh={handleRefresh}
      />

      {/* Historical Sessions Section - Bottom */}
      {/* Filter Panel */}
      <FilterPanel
        filters={filters}
        onFiltersChange={handleFiltersChange}
        statusCounts={statusCounts}
        availableAgentTypes={availableAgentTypes}
      />

      {/* Virtualized Historical Sessions List */}
      <VirtualizedSessionGrid
        sessions={historicalSessions}
        onSessionClick={handleSessionClick}
        loading={sessionsLoading}
        error={error}
        hasNextPage={hasNextPage}
        onLoadMore={loadMore}
                                 pagination={{
               page: pagination.page,
               per_page: pagination.per_page,
               total: pagination.total,
             }}
        height={600}
        itemHeight={120}
      />

      {/* Error Snackbar */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default React.memo(DashboardView); 