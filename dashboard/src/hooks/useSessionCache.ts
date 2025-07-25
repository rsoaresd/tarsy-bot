import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { SessionSummary, SessionTimeline, DashboardMetrics, SessionFilter } from '../types';
import { sessionCache, createFilterHash } from '../services/cacheManager';
import { dashboardApi, formatApiError } from '../services/api';

// Performance tracking hook
export function usePerformanceMonitoring() {
  const [metrics, setMetrics] = useState({
    renderCount: 0,
    lastRenderTime: 0,
    avgRenderTime: 0,
    cacheHitRate: 0,
    memoryUsage: 0,
  });

  const renderStartTime = useRef<number>(0);
  const renderTimes = useRef<number[]>([]);

  // Start performance measurement
  const startMeasure = useCallback(() => {
    renderStartTime.current = performance.now();
  }, []);

  // End performance measurement
  const endMeasure = useCallback(() => {
    if (renderStartTime.current > 0) {
      const renderTime = performance.now() - renderStartTime.current;
      renderTimes.current.push(renderTime);
      
      // Keep only last 10 measurements
      if (renderTimes.current.length > 10) {
        renderTimes.current.shift();
      }

      const avgTime = renderTimes.current.reduce((a, b) => a + b, 0) / renderTimes.current.length;
      const cacheStats = sessionCache.getStats();

      setMetrics(prev => ({
        renderCount: prev.renderCount + 1,
        lastRenderTime: Math.round(renderTime * 100) / 100,
        avgRenderTime: Math.round(avgTime * 100) / 100,
        cacheHitRate: cacheStats.hitRate,
        memoryUsage: cacheStats.memoryUsage,
      }));

      renderStartTime.current = 0;
    }
  }, []);

  return {
    metrics,
    startMeasure,
    endMeasure,
  };
}

// Cached session list hook with intelligent loading
export function useCachedSessionList(
  filters: SessionFilter,
  pagination: { page: number; page_size: number }
) {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasNextPage, setHasNextPage] = useState(false);
  
  const filterHash = useMemo(() => createFilterHash({ ...filters, ...pagination }), [filters, pagination]);
  const loadingRef = useRef(false);

  // Load sessions with caching
  const loadSessions = useCallback(async (useCache = true) => {
    if (loadingRef.current) return;

    // Check cache first
    if (useCache) {
      const cached = sessionCache.getSessionList(filterHash);
      if (cached) {
        setSessions(cached);
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);
      loadingRef.current = true;

      const response = await dashboardApi.getHistoricalSessions(filters, pagination);
      
      setSessions(response.sessions);
      setHasNextPage(response.has_next);
      
      // Cache the results
      sessionCache.setSessionList(filterHash, response.sessions);

    } catch (err) {
      console.error('Failed to load sessions:', err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [filterHash, filters, pagination]);

  // Force reload without cache
  const reloadSessions = useCallback(() => {
    sessionCache.invalidateSessionLists();
    loadSessions(false);
  }, [loadSessions]);

  // Load more sessions for infinite scroll
  const loadMore = useCallback(async () => {
    if (loadingRef.current || !hasNextPage) return;

    try {
      setLoading(true);
      loadingRef.current = true;

      const nextPage = { ...pagination, page: pagination.page + 1 };
      const response = await dashboardApi.getHistoricalSessions(filters, nextPage);
      
      const newSessions = [...sessions, ...response.sessions];
      setSessions(newSessions);
              setHasNextPage(response.has_next);
      
      // Update cache with combined results
      const combinedFilterHash = createFilterHash({ ...filters, ...nextPage });
      sessionCache.setSessionList(combinedFilterHash, newSessions);

    } catch (err) {
      console.error('Failed to load more sessions:', err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  }, [sessions, hasNextPage, filters, pagination]);

  // Auto-load on filter/pagination changes
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return {
    sessions,
    loading,
    error,
    hasNextPage,
    loadMore,
    reload: reloadSessions,
  };
}

// Cached session detail hook with preloading
export function useCachedSessionDetail(sessionId: string, preloadAdjacent = true) {
  const [session, setSession] = useState<SessionSummary | null>(null);
  const [timeline, setTimeline] = useState<SessionTimeline | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load session data with caching
  const loadSession = useCallback(async (useCache = true) => {
    if (!sessionId) return;

    // Check cache first
    if (useCache) {
      const cachedSession = sessionCache.getSessionSummary(sessionId);
      const cachedTimeline = sessionCache.getSessionTimeline(sessionId);
      
      if (cachedSession && cachedTimeline) {
        setSession(cachedSession);
        setTimeline(cachedTimeline);
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);

      // Load both summary and timeline in parallel
      const [sessionResult, timelineResult] = await Promise.all([
        dashboardApi.getSessionSummary(sessionId),
        dashboardApi.getSessionTimeline(sessionId),
      ]);

      setSession(sessionResult);
      setTimeline(timelineResult);

      // Cache the results
      sessionCache.setSessionSummary(sessionId, sessionResult);
      sessionCache.setSessionTimeline(sessionId, timelineResult);

    } catch (err) {
      console.error('Failed to load session:', err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Preload adjacent sessions (for faster navigation)
  const preloadAdjacentSessions = useCallback(async (currentSessionIds: string[]) => {
    if (!preloadAdjacent) return;

    const currentIndex = currentSessionIds.indexOf(sessionId);
    const adjacentIds = [
      currentSessionIds[currentIndex - 1],
      currentSessionIds[currentIndex + 1],
    ].filter(Boolean);

    // Preload adjacent sessions in background
    adjacentIds.forEach(async (id) => {
      if (!sessionCache.getSessionSummary(id) || !sessionCache.getSessionTimeline(id)) {
        try {
          const [summaryResult, timelineResult] = await Promise.all([
            dashboardApi.getSessionSummary(id),
            dashboardApi.getSessionTimeline(id),
          ]);
          
          sessionCache.setSessionSummary(id, summaryResult);
          sessionCache.setSessionTimeline(id, timelineResult);
        } catch (err) {
          // Silently fail preloading
          console.debug(`Failed to preload session ${id}:`, err);
        }
      }
    });
  }, [sessionId, preloadAdjacent]);

  // Force reload without cache
  const reloadSession = useCallback(() => {
    sessionCache.invalidateSession(sessionId);
    loadSession(false);
  }, [sessionId, loadSession]);

  // Auto-load on session ID changes
  useEffect(() => {
    loadSession();
  }, [loadSession]);

  return {
    session,
    timeline,
    loading,
    error,
    reload: reloadSession,
    preloadAdjacent: preloadAdjacentSessions,
  };
}

// Dashboard metrics hook with caching
export function useCachedDashboardMetrics() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMetrics = useCallback(async (useCache = true) => {
    // Check cache first
    if (useCache) {
      const cached = sessionCache.getDashboardMetrics();
      if (cached) {
        setMetrics(cached);
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);

      const result = await dashboardApi.getDashboardMetrics();
      setMetrics(result);
      
      // Cache the results
      sessionCache.setDashboardMetrics(result);

    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Force reload without cache
  const reloadMetrics = useCallback(() => {
    sessionCache.invalidateDashboard();
    loadMetrics(false);
  }, [loadMetrics]);

  // Auto-load on mount
  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  // Auto-refresh metrics every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadMetrics(false); // Always fetch fresh data for metrics
    }, 30000);

    return () => clearInterval(interval);
  }, [loadMetrics]);

  return {
    metrics,
    loading,
    error,
    reload: reloadMetrics,
  };
}

// Active sessions hook with frequent updates
export function useCachedActiveSessions() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadActiveSessions = useCallback(async (useCache = true) => {
    // Check cache first (but with shorter TTL for active data)
    if (useCache) {
      const cached = sessionCache.getActiveSessions();
      if (cached) {
        setSessions(cached);
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);

      const result = await dashboardApi.getActiveSessions();
      setSessions(result);
      
      // Cache the results with short TTL
      sessionCache.setActiveSessions(result);

    } catch (err) {
      console.error('Failed to load active sessions:', err);
      setError(formatApiError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // Force reload without cache
  const reloadActiveSessions = useCallback(() => {
    sessionCache.invalidateDashboard();
    loadActiveSessions(false);
  }, [loadActiveSessions]);

  // Auto-load on mount
  useEffect(() => {
    loadActiveSessions();
  }, [loadActiveSessions]);

  // Auto-refresh active sessions every 15 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadActiveSessions(false); // Always fetch fresh data for active sessions
    }, 15000);

    return () => clearInterval(interval);
  }, [loadActiveSessions]);

  return {
    sessions,
    loading,
    error,
    reload: reloadActiveSessions,
  };
}

// Cache statistics hook for monitoring
export function useCacheStats() {
  const [stats, setStats] = useState(() => sessionCache.getStats());

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(sessionCache.getStats());
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return stats;
} 