/**
 * API client for dashboard backend communication
 * Handles REST API calls for session data, metrics, and historical information
 */

import { SessionSummary, SessionTimeline, InteractionDetail, DashboardMetrics, SessionFilter, PaginationOptions } from '../types';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public retryable: boolean = false
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function formatApiError(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}

interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableStatuses: number[];
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  monitoringWindow: number;
}

class CircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private requestCount = 0;
  private windowStart = Date.now();

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.shouldReject()) {
      throw new ApiError('Circuit breaker is open', 503, 'CIRCUIT_BREAKER_OPEN', false);
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldReject(): boolean {
    const now = Date.now();
    
    // Reset monitoring window
    if (now - this.windowStart > this.config.monitoringWindow) {
      this.windowStart = now;
      this.requestCount = 0;
    }

    if (this.state === 'open') {
      if (now - this.lastFailureTime > this.config.resetTimeout) {
        this.state = 'half-open';
        return false;
      }
      return true;
    }

    return false;
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
    this.requestCount++;
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();
    this.requestCount++;

    if (this.failures >= this.config.failureThreshold) {
      this.state = 'open';
    }
  }

  getState(): { state: string; failures: number; requestCount: number } {
    return {
      state: this.state,
      failures: this.failures,
      requestCount: this.requestCount,
    };
  }
}

class ApiClient {
  private baseURL: string;
  private defaultRetryConfig: RetryConfig;
  private circuitBreaker: CircuitBreaker;
  private isOnline: boolean = navigator.onLine;

  constructor(baseURL: string = '/api') {
    this.baseURL = baseURL;
    this.defaultRetryConfig = {
      maxAttempts: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      backoffMultiplier: 2,
      retryableStatuses: [408, 429, 500, 502, 503, 504],
    };
    this.circuitBreaker = new CircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 30000,
      monitoringWindow: 60000,
    });

    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
    });
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  private async delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private calculateDelay(attempt: number, config: RetryConfig): number {
    const exponentialDelay = config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1);
    const jitteredDelay = exponentialDelay * (0.5 + Math.random() * 0.5); // Add jitter
    return Math.min(jitteredDelay, config.maxDelay);
  }

  private shouldRetry(error: unknown, attempt: number, config: RetryConfig): boolean {
    if (attempt >= config.maxAttempts) return false;
    
    if (isApiError(error)) {
      return error.retryable || (error.status ? config.retryableStatuses.includes(error.status) : false);
    }
    
    // Network errors are generally retryable
    return true;
  }

  private async executeWithRetry<T>(
    operation: () => Promise<T>,
    config: RetryConfig = this.defaultRetryConfig
  ): Promise<T> {
    let lastError: unknown;

    for (let attempt = 1; attempt <= config.maxAttempts; attempt++) {
      try {
        return await this.circuitBreaker.execute(operation);
      } catch (error) {
        lastError = error;
        
        if (!this.shouldRetry(error, attempt, config)) {
          throw error;
        }

        if (attempt < config.maxAttempts) {
          const delay = this.calculateDelay(attempt, config);
          await this.delay(delay);
        }
      }
    }

    throw lastError;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    retryConfig?: Partial<RetryConfig>
  ): Promise<T> {
    // Check online status
    if (!this.isOnline) {
      throw new ApiError('No internet connection', 0, 'OFFLINE', true);
    }

    const config = { ...this.defaultRetryConfig, ...retryConfig };
    
    const operation = async (): Promise<T> => {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const isRetryable = config.retryableStatuses.includes(response.status);
        let message = `HTTP ${response.status}`;
        
        try {
          const errorData = await response.json();
          message = errorData.message || errorData.detail || message;
        } catch {
          // Use default message if response parsing fails
        }

        throw new ApiError(message, response.status, 'HTTP_ERROR', isRetryable);
      }

      try {
        return await response.json();
      } catch (error) {
        throw new ApiError('Invalid JSON response', response.status, 'PARSE_ERROR', false);
      }
    };

    return this.executeWithRetry(operation, config);
  }

  async get<T>(endpoint: string, retryConfig?: Partial<RetryConfig>): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'GET' }, retryConfig);
  }

  async post<T>(endpoint: string, data?: any, retryConfig?: Partial<RetryConfig>): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, retryConfig);
  }

  async put<T>(endpoint: string, data?: any, retryConfig?: Partial<RetryConfig>): Promise<T> {
    return this.makeRequest<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }, retryConfig);
  }

  async delete<T>(endpoint: string, retryConfig?: Partial<RetryConfig>): Promise<T> {
    return this.makeRequest<T>(endpoint, { method: 'DELETE' }, retryConfig);
  }

  // Get current connection and circuit breaker status
  getStatus() {
    return {
      isOnline: this.isOnline,
      circuitBreaker: this.circuitBreaker.getState(),
    };
  }
}

// Enhanced retry helper for specific operations
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxAttempts: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: unknown;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      
      if (attempt < maxAttempts) {
        const delay = baseDelay * Math.pow(2, attempt - 1);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}

// Create API client instance
const apiClient = new ApiClient();

// Dashboard API service with enhanced error handling and caching fallbacks
export const dashboardApi = {
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      return await apiClient.get<DashboardMetrics>('/v1/history/metrics', {
        maxAttempts: 2, // Metrics are less critical, fewer retries
        baseDelay: 500,
      });
    } catch (error) {
      // Provide fallback data for graceful degradation
      if (isApiError(error) && error.code === 'OFFLINE') {
        return {
          active_sessions: 0,
          completed_sessions: 0,
          failed_sessions: 0,
          total_interactions: 0,
          avg_session_duration: 0,
          error_rate: 0,
          last_updated: new Date().toISOString(),
        };
      }
      throw error;
    }
  },

  async getHistoricalSessions(
    filters: SessionFilter,
    pagination: { page: number; page_size: number }
  ): Promise<{ sessions: SessionSummary[]; has_next: boolean; total: number }> {
    const params = new URLSearchParams({
      page: pagination.page.toString(),
      page_size: pagination.page_size.toString(),
      ...(filters.search_query && { search: filters.search_query }),
      ...(filters.status && filters.status.length > 0 && { status: filters.status.join(',') }),
      ...(filters.agent_type && filters.agent_type.length > 0 && { agent_type: filters.agent_type.join(',') }),
      ...(filters.date_range && { 
        start_date: filters.date_range.start, 
        end_date: filters.date_range.end 
      }),
    });

    return await apiClient.get<{ sessions: SessionSummary[]; has_next: boolean; total: number }>(
      `/v1/history/sessions?${params}`
    );
  },

  async getSessionSummary(sessionId: string): Promise<SessionSummary> {
    return await apiClient.get<SessionSummary>(`/v1/history/sessions/${sessionId}`);
  },

  async getSessionTimeline(sessionId: string): Promise<SessionTimeline> {
    return await apiClient.get<SessionTimeline>(`/v1/history/sessions/${sessionId}/timeline`);
  },

  async getActiveSessions(): Promise<SessionSummary[]> {
    try {
      return await apiClient.get<SessionSummary[]>('/v1/history/active-sessions', {
        maxAttempts: 2,
        baseDelay: 500,
      });
    } catch (error) {
      // Return empty array for graceful degradation
      if (isApiError(error) && (error.code === 'OFFLINE' || error.status === 503)) {
        return [];
      }
      throw error;
    }
  },

  async getSystemHealth(): Promise<{ status: string; components: Record<string, any> }> {
    return await apiClient.get<{ status: string; components: Record<string, any> }>('/health');
  },

  async getFilterOptions(): Promise<{
    agent_types: string[];
    status_options: string[];
    time_ranges: { label: string; value: string }[];
  }> {
    try {
      return await apiClient.get<{
        agent_types: string[];
        status_options: string[];
        time_ranges: { label: string; value: string }[];
      }>('/v1/history/filter-options');
    } catch (error) {
      // Provide fallback filter options
      return {
        agent_types: ['kubernetes_agent', 'general_agent'],
        status_options: ['active', 'completed', 'failed', 'timeout'],
        time_ranges: [
          { label: 'Last Hour', value: '1h' },
          { label: 'Last 24 Hours', value: '24h' },
          { label: 'Last Week', value: '7d' },
          { label: 'Last Month', value: '30d' },
        ],
      };
    }
  },

  async exportSessionData(sessionId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await fetch(`/api/v1/history/sessions/${sessionId}/export?format=${format}`);
    if (!response.ok) {
      throw new ApiError(`Export failed: ${response.statusText}`, response.status);
    }
    return await response.blob();
  },

  async searchSessions(query: string, limit: number = 10): Promise<SessionSummary[]> {
    return await apiClient.get<SessionSummary[]>(
      `/v1/history/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
  },

  // Get API client status for debugging/monitoring
  getConnectionStatus() {
    return apiClient.getStatus();
  },
}; 