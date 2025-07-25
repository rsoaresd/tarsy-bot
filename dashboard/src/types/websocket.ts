/**
 * WebSocket type definitions for dashboard client
 * Matches backend websocket_models.py structure
 */

// WebSocket Message Types
export type WebSocketMessageType = 
  | 'subscribe'
  | 'unsubscribe'
  | 'dashboard_update'
  | 'session_update'
  | 'system_health'
  | 'alert_status'
  | 'ping'
  | 'pong'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  channel: string;
  data: any;
  timestamp?: string;
}

export interface SubscriptionMessage {
  type: 'subscribe' | 'unsubscribe';
  channel: string;
  data: {
    action: 'subscribe' | 'unsubscribe';
    channel: string;
    options?: SubscriptionOptions;
  };
  timestamp?: string;
}

export interface SubscriptionResponse {
  type: 'subscription_response';
  channel: string;
  success: boolean;
  action: 'subscribe' | 'unsubscribe';
  message?: string;
  timestamp: string;
}

export interface ConnectionEstablished {
  type: 'connection_established';
  channel: 'system';
  data: {
    connection_id: string;
    user_id: string;
    timestamp: string;
  };
}

export interface ErrorMessage {
  type: 'error';
  channel: string;
  data: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

// Dashboard-specific message types
export interface DashboardUpdate {
  type: 'dashboard_update';
  channel: 'dashboard_updates';
  data: {
    metrics_changed: boolean;
    sessions_changed: boolean;
    active_alerts_changed: boolean;
    timestamp: string;
  };
}

export interface SessionUpdate {
  type: 'session_update';
  channel: string; // session_{sessionId}
  data: {
    session_id: string;
    status: 'active' | 'completed' | 'failed' | 'timeout';
    progress?: number;
    current_step?: string;
    timestamp: string;
    interaction_type?: 'llm' | 'mcp';
    interaction_data?: any;
  };
}

export interface SystemHealthUpdate {
  type: 'system_health';
  channel: 'system_health';
  data: {
    status: 'healthy' | 'degraded' | 'unhealthy';
    components: Record<string, {
      status: 'healthy' | 'degraded' | 'unhealthy';
      last_check: string;
      details?: any;
    }>;
    timestamp: string;
  };
}

export interface AlertStatusUpdate {
  type: 'alert_status';
  channel: 'dashboard_updates';
  data: {
    alert_id: string;
    status: 'processing' | 'completed' | 'failed' | 'timeout';
    progress: number;
    current_step: string;
    timestamp: string;
  };
}

// Channel naming utilities
export class ChannelType {
  static readonly DASHBOARD_UPDATES = 'dashboard_updates';
  static readonly SYSTEM_HEALTH = 'system_health';
  
  static sessionChannel(sessionId: string): string {
    return `session_${sessionId}`;
  }
  
  static userChannel(userId: string): string {
    return `user_${userId}`;
  }
}

// WebSocket State Types
export type WebSocketState = 'disconnected' | 'connecting' | 'connected' | 'error';

// WebSocket Configuration
export interface WebSocketConfig {
  url: string;
  userId?: string;
  connectionTimeout?: number;
  messageTimeout?: number;
  reconnection?: {
    maxAttempts: number;
    baseDelay: number;
    maxDelay: number;
    backoffMultiplier: number;
    jitterFactor: number;
  };
}

// Subscription Options
export interface SubscriptionOptions {
  autoResubscribe?: boolean;
  bufferMessages?: boolean;
  maxBuffer?: number;
  priority?: 'high' | 'normal' | 'low';
}

// Event Handlers
export interface WebSocketEventHandlers {
  onConnect?: () => void;
  onDisconnect?: (event?: CloseEvent) => void;
  onError?: (error: Error) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onStateChange?: (state: WebSocketState) => void;
  onSubscriptionConfirmed?: (channel: string) => void;
  onSubscriptionError?: (channel: string, error: string) => void;
}

// Queued Messages
export interface QueuedMessage {
  message: any;
  channel: string;
  timestamp: number;
  retries?: number;
  priority?: number;
}

// WebSocket Statistics
export interface WebSocketStats {
  currentState: WebSocketState;
  totalConnections: number;
  totalDisconnections: number;
  totalReconnections: number;
  messagesReceived: number;
  messagesSent: number;
  lastConnected: number;
  lastDisconnected: number;
  reconnectAttempt: number;
  subscriptionCount: number;
  queueStats: {
    size: number;
    highPriority: number;
    lowPriority: number;
  };
  circuitBreakerState: {
    state: string;
    failures: number;
    lastFailureTime: number;
  };
  isOnline: boolean;
  connectionId: string;
  lastHeartbeat: number;
}

// Hook return types
export interface WebSocketHookReturn {
  state: WebSocketState;
  isConnected: boolean;
  error: Error | null;
  stats: WebSocketStats | null;
  forceReconnect: () => Promise<void>;
  disconnect: () => void;
  manager: any; // MultiplexedWebSocketManager
}

export interface SubscriptionHookReturn {
  isSubscribed: boolean;
  error: string | null;
  subscribe: () => void;
  unsubscribe: () => void;
  retryCount: number;
}

export interface DashboardUpdatesHookReturn {
  isSubscribed: boolean;
  updates: any;
  lastUpdateTime: Date | null;
  error: string | null;
  retryCount: number;
}

export interface SessionUpdatesHookReturn {
  isSubscribed: boolean;
  updates: any;
  error: string | null;
  subscribe: () => void;
  unsubscribe: () => void;
  retryCount: number;
}

export interface SystemHealthHookReturn {
  isSubscribed: boolean;
  health: any;
  error: string | null;
  retryCount: number;
}

export interface WebSocketStatusHookReturn extends WebSocketHookReturn {
  isHealthy: boolean;
  canRetry: boolean;
}

export interface ErrorRecoveryHookReturn {
  error: Error | null;
  isRecovering: boolean;
  recoveryAttempts: number;
  canRecover: boolean;
  attemptRecovery: () => Promise<void>;
} 