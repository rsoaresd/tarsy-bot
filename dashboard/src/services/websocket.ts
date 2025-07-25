import type { WebSocketMessage, SessionUpdate } from '../types';

type WebSocketEventHandler = (data: SessionUpdate) => void;
type WebSocketErrorHandler = (error: Event) => void;
type WebSocketCloseHandler = (event: CloseEvent) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private permanentlyDisabled = false;
  private userId: string;
  private eventHandlers: {
    sessionUpdate: WebSocketEventHandler[];
    sessionCompleted: WebSocketEventHandler[];
    sessionFailed: WebSocketEventHandler[];
    dashboardUpdate: WebSocketEventHandler[]; // Add handler for dashboard updates
    connectionChange: Array<(connected: boolean) => void>; // Add connection change handler
    error: WebSocketErrorHandler[];
    close: WebSocketCloseHandler[];
  } = {
    sessionUpdate: [],
    sessionCompleted: [],
    sessionFailed: [],
    dashboardUpdate: [], // Initialize dashboard update handlers
    connectionChange: [], // Initialize connection change handlers
    error: [],
    close: [],
  };

  constructor() {
    // Generate a unique user ID for this dashboard session
    this.userId = 'dashboard-' + Math.random().toString(36).substr(2, 9);
    
    // WebSocket URL configuration
    // In development, use relative URLs to work with Vite proxy
    // In production, use the full URL from environment variables
    if (import.meta.env.DEV) {
      // Development: use current host with ws protocol
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      this.url = `${protocol}//${host}/ws/dashboard/${this.userId}`;
    } else {
      // Production: use environment variable
      const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
      this.url = `${wsBaseUrl}/ws/dashboard/${this.userId}`;
    }
  }

  /**
   * Connect to WebSocket with automatic reconnection
   */
  connect(): void {
    if (this.permanentlyDisabled) {
      console.log('WebSocket permanently disabled (endpoint not available)');
      return;
    }

    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return;
    }

    this.isConnecting = true;
    console.log('🔌 Connecting to WebSocket:', this.url);

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('🎉 WebSocket connected successfully!');
        this.isConnecting = false;
        this.reconnectAttempts = 0;

        // Notify connection change handlers
        this.eventHandlers.connectionChange.forEach(handler => handler(true));

        // Subscribe to dashboard updates
        const subscribeMessage = {
          type: 'subscribe',
          channel: 'dashboard_updates'
        };
        console.log('📤 Sending subscription message:', subscribeMessage);
        this.send(subscribeMessage);
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📥 WebSocket message received:', message);
          this.handleMessage(message);
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error, 'Raw data:', event.data);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.isConnecting = false;
        this.eventHandlers.error.forEach(handler => handler(error));
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnecting = false;
        this.ws = null;
        this.eventHandlers.close.forEach(handler => handler(event));

        // Notify connection change handlers
        this.eventHandlers.connectionChange.forEach(handler => handler(false));

        // Check if we should attempt to reconnect
        if (event.code !== 1000) {
          // On first failure, check if endpoint exists
          if (this.reconnectAttempts === 0) {
            this.checkEndpointExists().then(exists => {
              if (!exists) {
                console.log('WebSocket endpoint not available, disabling WebSocket features');
                this.permanentlyDisabled = true;
                return;
              }
              
              // Endpoint exists but connection failed, try to reconnect
              if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
              }
            });
          } else if (this.reconnectAttempts < this.maxReconnectAttempts) {
            // Subsequent failures - just retry
            this.scheduleReconnect();
          } else {
            console.log('Max WebSocket reconnection attempts reached, disabling');
            this.permanentlyDisabled = true;
          }
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.isConnecting = false;
    }
  }

  /**
   * Check if WebSocket endpoint exists by testing HTTP endpoint via proxy
   */
  private async checkEndpointExists(): Promise<boolean> {
    try {
      // Test if the WebSocket endpoint path exists by checking a simple endpoint
      // Since WebSocket endpoints don't respond to HTTP, we'll just check if we get a reasonable response
      const response = await fetch(`/ws/dashboard/${this.userId}`);
      
      // If we get 404, the endpoint doesn't exist
      if (response.status === 404) {
        return false;
      }
      
      // Any other response (including WebSocket upgrade errors) suggests the endpoint exists
      return true;
    } catch (error) {
      console.log('Endpoint check failed, assuming endpoint might exist:', error);
      // Network error, assume endpoint might exist
      return true;
    }
  }

  /**
   * Disconnect from WebSocket
   */
  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }

    this.isConnecting = false;
    this.reconnectAttempts = 0;
  }

  /**
   * Send message to WebSocket
   */
  private send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('🔄 Processing WebSocket message:', message);
    
    if (!message.data) {
      console.log('⚠️  Message has no data property, skipping handlers');
      return;
    }

    switch (message.type) {
      case 'session_update':
        console.log('📈 Handling session_update, calling', this.eventHandlers.sessionUpdate.length, 'handlers');
        this.eventHandlers.sessionUpdate.forEach(handler => handler(message.data!));
        break;
      case 'session_completed':
        console.log('✅ Handling session_completed, calling', this.eventHandlers.sessionCompleted.length, 'handlers');
        this.eventHandlers.sessionCompleted.forEach(handler => handler(message.data!));
        break;
      case 'session_failed':
        console.log('❌ Handling session_failed, calling', this.eventHandlers.sessionFailed.length, 'handlers');
        this.eventHandlers.sessionFailed.forEach(handler => handler(message.data!));
        break;
      case 'dashboard_update':
        console.log('📊 Handling dashboard_update, calling', this.eventHandlers.dashboardUpdate.length, 'handlers');
        this.eventHandlers.dashboardUpdate.forEach(handler => handler(message.data!));
        break;
      case 'ping':
        console.log('🏓 Received ping, responding with pong');
        // Respond to ping with pong
        this.send({ type: 'pong' });
        break;
      case 'connection_established':
        console.log('🔗 Connection established message received');
        break;
      case 'subscription_response':
        console.log('📋 Subscription response received:', message.data);
        break;
      default:
        console.log('❓ Unknown message type:', message.type);
    }
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.permanentlyDisabled) {
      return;
    }

    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000); // Exponential backoff, max 10s
    
    console.log(`WebSocket reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  /**
   * Add event listener for session updates
   */
  onSessionUpdate(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.sessionUpdate.push(handler);
    return () => {
      const index = this.eventHandlers.sessionUpdate.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.sessionUpdate.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for session completion
   */
  onSessionCompleted(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.sessionCompleted.push(handler);
    return () => {
      const index = this.eventHandlers.sessionCompleted.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.sessionCompleted.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for session failure
   */
  onSessionFailed(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.sessionFailed.push(handler);
    return () => {
      const index = this.eventHandlers.sessionFailed.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.sessionFailed.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for dashboard updates
   */
  onDashboardUpdate(handler: WebSocketEventHandler): () => void {
    this.eventHandlers.dashboardUpdate.push(handler);
    return () => {
      const index = this.eventHandlers.dashboardUpdate.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.dashboardUpdate.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for connection errors
   */
  onError(handler: WebSocketErrorHandler): () => void {
    this.eventHandlers.error.push(handler);
    return () => {
      const index = this.eventHandlers.error.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.error.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for connection close
   */
  onClose(handler: WebSocketCloseHandler): () => void {
    this.eventHandlers.close.push(handler);
    return () => {
      const index = this.eventHandlers.close.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.close.splice(index, 1);
      }
    };
  }

  /**
   * Add event listener for connection state changes
   */
  onConnectionChange(handler: (connected: boolean) => void): () => void {
    this.eventHandlers.connectionChange.push(handler);
    return () => {
      const index = this.eventHandlers.connectionChange.indexOf(handler);
      if (index > -1) {
        this.eventHandlers.connectionChange.splice(index, 1);
      }
    };
  }

  /**
   * Get current connection state
   */
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * Check if connected
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Check if WebSocket is permanently disabled
   */
  get isDisabled(): boolean {
    return this.permanentlyDisabled;
  }

  /**
   * Get the current user ID
   */
  get currentUserId(): string {
    return this.userId;
  }
}

// Export singleton instance
export const webSocketService = new WebSocketService(); 