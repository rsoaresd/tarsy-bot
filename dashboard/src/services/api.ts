import axios, { type AxiosInstance, AxiosError } from 'axios';
import type { SessionsResponse } from '../types';

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
   * Fetch all sessions (newest first)
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