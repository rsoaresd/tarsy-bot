import { SessionSummary, SessionTimeline, InteractionDetail, DashboardMetrics } from '../types';

// Cache entry interface
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
  accessed: number; // Last access time for LRU
}

// Cache configuration
interface CacheConfig {
  maxSize: number;
  defaultTTL: number;
  cleanupInterval: number;
}

// Cache statistics
interface CacheStats {
  hits: number;
  misses: number;
  size: number;
  hitRate: number;
  memoryUsage: number;
}

/**
 * Generic cache manager with TTL, LRU eviction, and performance monitoring
 */
class CacheManager {
  private cache = new Map<string, CacheEntry<any>>();
  private stats = {
    hits: 0,
    misses: 0,
  };
  private cleanupTimer: NodeJS.Timeout | null = null;

  constructor(private config: CacheConfig) {
    this.startCleanup();
  }

  /**
   * Get cached value with TTL check
   */
  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    
    if (!entry) {
      this.stats.misses++;
      return null;
    }

    const now = Date.now();
    
    // Check if entry has expired
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      this.stats.misses++;
      return null;
    }

    // Update access time for LRU
    entry.accessed = now;
    this.stats.hits++;
    
    return entry.data;
  }

  /**
   * Set cached value with optional custom TTL
   */
  set<T>(key: string, data: T, customTTL?: number): void {
    const now = Date.now();
    const ttl = customTTL || this.config.defaultTTL;

    // Check if we need to evict items (LRU)
    if (this.cache.size >= this.config.maxSize) {
      this.evictLRU();
    }

    this.cache.set(key, {
      data,
      timestamp: now,
      ttl,
      accessed: now,
    });
  }

  /**
   * Check if key exists and is not expired
   */
  has(key: string): boolean {
    return this.get(key) !== null;
  }

  /**
   * Delete specific cache entry
   */
  delete(key: string): boolean {
    return this.cache.delete(key);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.stats.hits = 0;
    this.stats.misses = 0;
  }

  /**
   * Invalidate entries matching pattern
   */
  invalidatePattern(pattern: RegExp): number {
    let count = 0;
    
    for (const key of this.cache.keys()) {
      if (pattern.test(key)) {
        this.cache.delete(key);
        count++;
      }
    }
    
    return count;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0;
    
    // Estimate memory usage (rough calculation)
    let memoryUsage = 0;
    for (const [key, entry] of this.cache.entries()) {
      memoryUsage += key.length * 2; // String characters are 2 bytes
      memoryUsage += JSON.stringify(entry.data).length * 2;
      memoryUsage += 32; // Overhead for timestamps and metadata
    }

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      size: this.cache.size,
      hitRate: Math.round(hitRate * 100) / 100,
      memoryUsage: Math.round(memoryUsage / 1024), // KB
    };
  }

  /**
   * Evict least recently used entry
   */
  private evictLRU(): void {
    let oldestKey: string | null = null;
    let oldestAccess = Date.now();

    for (const [key, entry] of this.cache.entries()) {
      if (entry.accessed < oldestAccess) {
        oldestAccess = entry.accessed;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
    }
  }

  /**
   * Clean up expired entries
   */
  private cleanup(): void {
    const now = Date.now();
    const keysToDelete: string[] = [];

    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  /**
   * Start periodic cleanup
   */
  private startCleanup(): void {
    this.cleanupTimer = setInterval(() => {
      this.cleanup();
    }, this.config.cleanupInterval);
  }

  /**
   * Stop cleanup timer
   */
  destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = null;
    }
    this.clear();
  }
}

/**
 * Specialized session cache with domain-specific methods
 */
export class SessionCacheManager {
  private cache: CacheManager;

  // Cache TTL configurations (in milliseconds)
  private static readonly TTL = {
    SESSION_SUMMARY: 5 * 60 * 1000,    // 5 minutes
    SESSION_TIMELINE: 10 * 60 * 1000,  // 10 minutes
    SESSION_LIST: 2 * 60 * 1000,       // 2 minutes
    DASHBOARD_METRICS: 30 * 1000,      // 30 seconds
    ACTIVE_SESSIONS: 15 * 1000,        // 15 seconds (more frequent for active data)
  };

  constructor() {
    this.cache = new CacheManager({
      maxSize: 1000,                    // Store up to 1000 entries
      defaultTTL: SessionCacheManager.TTL.SESSION_SUMMARY,
      cleanupInterval: 60 * 1000,       // Cleanup every minute
    });
  }

  /**
   * Session summary caching
   */
  getSessionSummary(sessionId: string): SessionSummary | null {
    return this.cache.get(`session:${sessionId}`);
  }

  setSessionSummary(sessionId: string, summary: SessionSummary): void {
    this.cache.set(`session:${sessionId}`, summary, SessionCacheManager.TTL.SESSION_SUMMARY);
  }

  /**
   * Session timeline caching
   */
  getSessionTimeline(sessionId: string): SessionTimeline | null {
    return this.cache.get(`timeline:${sessionId}`);
  }

  setSessionTimeline(sessionId: string, timeline: SessionTimeline): void {
    this.cache.set(`timeline:${sessionId}`, timeline, SessionCacheManager.TTL.SESSION_TIMELINE);
  }

  /**
   * Session list caching (with filter hash)
   */
  getSessionList(filterHash: string): SessionSummary[] | null {
    return this.cache.get(`sessions:${filterHash}`);
  }

  setSessionList(filterHash: string, sessions: SessionSummary[]): void {
    this.cache.set(`sessions:${filterHash}`, sessions, SessionCacheManager.TTL.SESSION_LIST);
  }

  /**
   * Dashboard metrics caching
   */
  getDashboardMetrics(): DashboardMetrics | null {
    return this.cache.get('dashboard:metrics');
  }

  setDashboardMetrics(metrics: DashboardMetrics): void {
    this.cache.set('dashboard:metrics', metrics, SessionCacheManager.TTL.DASHBOARD_METRICS);
  }

  /**
   * Active sessions caching
   */
  getActiveSessions(): SessionSummary[] | null {
    return this.cache.get('dashboard:active');
  }

  setActiveSessions(sessions: SessionSummary[]): void {
    this.cache.set('dashboard:active', sessions, SessionCacheManager.TTL.ACTIVE_SESSIONS);
  }

  /**
   * Invalidate session-related cache entries
   */
  invalidateSession(sessionId: string): void {
    this.cache.delete(`session:${sessionId}`);
    this.cache.delete(`timeline:${sessionId}`);
    
    // Invalidate all session lists since they might contain this session
    this.cache.invalidatePattern(/^sessions:/);
    
    // Invalidate active sessions and metrics
    this.cache.delete('dashboard:active');
    this.cache.delete('dashboard:metrics');
  }

  /**
   * Invalidate all session lists (when filters change)
   */
  invalidateSessionLists(): void {
    this.cache.invalidatePattern(/^sessions:/);
  }

  /**
   * Invalidate dashboard data
   */
  invalidateDashboard(): void {
    this.cache.delete('dashboard:active');
    this.cache.delete('dashboard:metrics');
  }

  /**
   * Preload frequently accessed data
   */
  async preloadSession(sessionId: string, loadFn: () => Promise<{
    summary: SessionSummary;
    timeline: SessionTimeline;
  }>): Promise<void> {
    // Only preload if not already cached
    if (!this.getSessionSummary(sessionId) || !this.getSessionTimeline(sessionId)) {
      try {
        const { summary, timeline } = await loadFn();
        this.setSessionSummary(sessionId, summary);
        this.setSessionTimeline(sessionId, timeline);
      } catch (error) {
        console.warn(`Failed to preload session ${sessionId}:`, error);
      }
    }
  }

  /**
   * Get cache performance statistics
   */
  getStats(): CacheStats {
    return this.cache.getStats();
  }

  /**
   * Clear all cached data
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    this.cache.destroy();
  }
}

/**
 * Create filter hash for consistent caching
 */
export function createFilterHash(filters: Record<string, any>): string {
  // Sort keys to ensure consistent hash regardless of object property order
  const sortedKeys = Object.keys(filters).sort();
  const normalized = sortedKeys.map(key => `${key}:${JSON.stringify(filters[key])}`).join('|');
  
  // Simple hash function (for development - use crypto in production)
  let hash = 0;
  for (let i = 0; i < normalized.length; i++) {
    const char = normalized.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  
  return hash.toString(36);
}

// Export singleton instance
export const sessionCache = new SessionCacheManager(); 