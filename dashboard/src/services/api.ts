import axios, { type AxiosInstance, AxiosError } from 'axios';
import type { SessionsResponse, Session } from '../types';

// API base URL configuration
// In development with Vite proxy, use relative URLs
// In production, use the full URL from environment variables
const API_BASE_URL = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error);
        
        if (error.response) {
          // Server responded with error status
          const message = (error.response.data as any)?.error || `Server error: ${error.response.status}`;
          return Promise.reject(new Error(message));
        } else if (error.request) {
          // Network error
          return Promise.reject(new Error('Network error: Unable to connect to server'));
        } else {
          // Other error
          return Promise.reject(new Error('Request failed'));
        }
      }
    );
  }

  /**
   * Fetch all sessions (newest first) - Phase 1 method
   * For Phase 1, we fetch all sessions without pagination
   */
  async getSessions(): Promise<SessionsResponse> {
    try {
      const response = await this.client.get<SessionsResponse>('/api/v1/history/sessions');
      
      // The backend returns the SessionsResponse directly, not wrapped in data
      if (response.data && typeof response.data === 'object' && 'sessions' in response.data) {
        return response.data;
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
      throw error instanceof Error ? error : new Error('Failed to fetch sessions');
    }
  }

  /**
   * Fetch active sessions only (Phase 2)
   * Backend returns a simple array of Session objects
   */
  async getActiveSessions(): Promise<{ active_sessions: Session[], total_count: number }> {
    try {
      const response = await this.client.get<Session[]>('/api/v1/history/active-sessions');
      
      // Debug logging to help troubleshoot filtering issues
      console.log('Active sessions API response:', {
        totalSessions: Array.isArray(response.data) ? response.data.length : 0,
        statuses: Array.isArray(response.data) ? response.data.map((s: any) => s.status) : [],
        url: response.config?.url
      });
      
      // Backend returns a simple array, so we need to wrap it in the expected format
      if (Array.isArray(response.data)) {
        return {
          active_sessions: response.data,
          total_count: response.data.length
        };
      } else {
        throw new Error('Invalid active sessions response format');
      }
    } catch (error) {
      console.error('Failed to fetch active sessions:', error);
      throw error instanceof Error ? error : new Error('Failed to fetch active sessions');
    }
  }

  /**
   * Fetch historical sessions (completed/failed) - Phase 2
   * Gets sessions with status 'completed' or 'failed'
   */
  async getHistoricalSessions(): Promise<SessionsResponse> {
    try {
      // Build query string manually to ensure proper FastAPI format
      const queryParams = new URLSearchParams();
      queryParams.append('status', 'completed');
      queryParams.append('status', 'failed');
      const url = `/api/v1/history/sessions?${queryParams.toString()}`;
      
      console.log('🔍 Historical sessions - Full URL:', url);
      
      const response = await this.client.get<SessionsResponse>(url);
      
      // Debug logging to help troubleshoot filtering issues
      console.log('Historical sessions API response:', {
        totalSessions: response.data?.sessions?.length || 0,
        statuses: response.data?.sessions?.map(s => s.status) || [],
        requestedUrl: response.config?.url,
        actualUrl: response.request?.responseURL || 'unknown',
        params: response.config?.params,
        method: response.config?.method,
        rawResponseData: response.data
      });
      
      if (response.data && typeof response.data === 'object' && 'sessions' in response.data) {
        return response.data;
      } else {
        throw new Error('Invalid historical sessions response format');
      }
    } catch (error) {
      console.error('Failed to fetch historical sessions:', error);
      throw error instanceof Error ? error : new Error('Failed to fetch historical sessions');
    }
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string }> {
    try {
      const response = await this.client.get('/api/v1/history/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error instanceof Error ? error : new Error('Health check failed');
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Helper function for error handling in components
export const handleAPIError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}; 