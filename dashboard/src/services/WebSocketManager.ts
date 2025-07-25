/**
 * Multiplexed WebSocket Manager for Dashboard
 * Handles connections, subscriptions, auto-reconnection, and message routing
 */

import {
  WebSocketMessage,
  SubscriptionMessage,
  WebSocketState,
  WebSocketConfig,
  SubscriptionOptions,
  WebSocketEventHandlers,
  QueuedMessage,
  ChannelType,
} from '../types/websocket';

interface ReconnectionConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  jitterFactor: number;
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  healthCheckInterval: number;
}

interface MessageQueueConfig {
  maxSize: number;
  priorityChannels: string[];
  ttl: number; // Time to live for queued messages
}

class WebSocketCircuitBreaker {
  private failures = 0;
  private lastFailureTime = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private healthCheckTimer?: NodeJS.Timeout;

  constructor(private config: CircuitBreakerConfig) {}

  canAttemptConnection(): boolean {
    const now = Date.now();

    if (this.state === 'closed') {
      return true;
    }

    if (this.state === 'open') {
      if (now - this.lastFailureTime > this.config.resetTimeout) {
        this.state = 'half-open';
        return true;
      }
      return false;
    }

    // half-open state - allow one attempt
    return true;
  }

  onConnectionSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
    this.clearHealthCheck();
  }

  onConnectionFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.config.failureThreshold) {
      this.state = 'open';
      this.scheduleHealthCheck();
    } else if (this.state === 'half-open') {
      this.state = 'open';
      this.scheduleHealthCheck();
    }
  }

  private scheduleHealthCheck(): void {
    this.clearHealthCheck();
    this.healthCheckTimer = setInterval(() => {
      if (this.state === 'open' && Date.now() - this.lastFailureTime > this.config.resetTimeout) {
        this.state = 'half-open';
      }
    }, this.config.healthCheckInterval);
  }

  private clearHealthCheck(): void {
    if (this.healthCheckTimer) {
      clearInterval(this.healthCheckTimer);
      this.healthCheckTimer = undefined;
    }
  }

  getState(): { state: string; failures: number; lastFailureTime: number } {
    return {
      state: this.state,
      failures: this.failures,
      lastFailureTime: this.lastFailureTime,
    };
  }

  destroy(): void {
    this.clearHealthCheck();
  }
}

class MessageQueue {
  private queue: Array<QueuedMessage & { timestamp: number; priority: number }> = [];
  private config: MessageQueueConfig;

  constructor(config: MessageQueueConfig) {
    this.config = config;
    // Periodically clean up expired messages
    setInterval(() => this.cleanup(), 10000);
  }

  enqueue(message: QueuedMessage): boolean {
    if (this.queue.length >= this.config.maxSize) {
      // Remove oldest low-priority message to make room
      const oldestLowPriorityIndex = this.queue.findIndex(m => m.priority === 0);
      if (oldestLowPriorityIndex !== -1) {
        this.queue.splice(oldestLowPriorityIndex, 1);
      } else {
        // Queue is full of high-priority messages, drop this one
        return false;
      }
    }

    const priority = this.config.priorityChannels.includes(message.channel) ? 1 : 0;
    this.queue.push({
      ...message,
      timestamp: Date.now(),
      priority,
    });

    // Sort by priority (high first), then by timestamp (oldest first)
    this.queue.sort((a, b) => {
      if (a.priority !== b.priority) {
        return b.priority - a.priority;
      }
      return a.timestamp - b.timestamp;
    });

    return true;
  }

  dequeueAll(): QueuedMessage[] {
    const messages = this.queue.map(({ priority, ...msg }) => msg);
    this.queue = [];
    return messages;
  }

  private cleanup(): void {
    const now = Date.now();
    this.queue = this.queue.filter(msg => now - msg.timestamp < this.config.ttl);
  }

  getStats(): { size: number; highPriority: number; lowPriority: number } {
    const highPriority = this.queue.filter(m => m.priority === 1).length;
    return {
      size: this.queue.length,
      highPriority,
      lowPriority: this.queue.length - highPriority,
    };
  }
}

export class MultiplexedWebSocketManager {
  private ws: WebSocket | null = null;
  private state: WebSocketState = 'disconnected';
  private subscriptions = new Map<string, Set<(message: any) => void>>();
  private eventHandlers: WebSocketEventHandlers = {};
  private messageQueue: MessageQueue;
  private circuitBreaker: WebSocketCircuitBreaker;
  private reconnectionConfig: ReconnectionConfig;
  private reconnectTimer?: NodeJS.Timeout;
  private reconnectAttempt = 0;
  private connectionId = '';
  private lastHeartbeat = 0;
  private heartbeatTimer?: NodeJS.Timeout;
  private pingInterval?: NodeJS.Timeout;
  private isOnline = navigator.onLine;
  private connectionStats = {
    totalConnections: 0,
    totalDisconnections: 0,
    totalReconnections: 0,
    messagesReceived: 0,
    messagesSent: 0,
    lastConnected: 0,
    lastDisconnected: 0,
  };

  constructor(private config: WebSocketConfig) {
    this.reconnectionConfig = {
      maxAttempts: config.reconnection?.maxAttempts ?? 10,
      baseDelay: config.reconnection?.baseDelay ?? 1000,
      maxDelay: config.reconnection?.maxDelay ?? 30000,
      backoffMultiplier: config.reconnection?.backoffMultiplier ?? 1.5,
      jitterFactor: config.reconnection?.jitterFactor ?? 0.3,
    };

    this.messageQueue = new MessageQueue({
      maxSize: 1000,
      priorityChannels: ['dashboard_updates', 'system_health'],
      ttl: 300000, // 5 minutes
    });

    this.circuitBreaker = new WebSocketCircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000,
      healthCheckInterval: 10000,
    });

    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
      if (this.state === 'disconnected') {
        this.connect();
      }
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.state = 'disconnected';
      this.notifyStateChange();
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      this.disconnect();
    });
  }

  async connect(): Promise<void> {
    if (this.state === 'connected' || this.state === 'connecting') {
      return;
    }

    if (!this.isOnline) {
      throw new Error('No internet connection');
    }

    if (!this.circuitBreaker.canAttemptConnection()) {
      throw new Error('Circuit breaker is open - too many connection failures');
    }

    this.state = 'connecting';
    this.notifyStateChange();

    try {
      await this.establishConnection();
      this.circuitBreaker.onConnectionSuccess();
      this.reconnectAttempt = 0;
      this.processQueuedMessages();
    } catch (error) {
      this.circuitBreaker.onConnectionFailure();
      this.handleConnectionError(error);
      throw error;
    }
  }

  private async establishConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const wsUrl = `${this.config.url}/${this.config.userId || 'anonymous'}`;
        console.log('WebSocket: Attempting to connect to:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        this.connectionStats.totalConnections++;

        const timeout = setTimeout(() => {
          this.ws?.close();
          reject(new Error('Connection timeout'));
        }, this.config.connectionTimeout || 10000);

        this.ws.onopen = () => {
          console.log('WebSocket: Connection opened successfully');
          clearTimeout(timeout);
          this.state = 'connected';
          this.connectionId = `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          this.connectionStats.lastConnected = Date.now();
          this.lastHeartbeat = Date.now();
          this.startHeartbeat();
          this.notifyStateChange();
          this.eventHandlers.onConnect?.();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket: Connection closed', event.code, event.reason);
          clearTimeout(timeout);
          this.handleClose(event);
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket: Connection error', error);
          clearTimeout(timeout);
          this.handleError(error);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private handleMessage(event: MessageEvent): void {
    try {
      this.connectionStats.messagesReceived++;
      const message: WebSocketMessage = JSON.parse(event.data);

      // Handle system messages
      if (message.type === 'ping') {
        this.send({ type: 'pong', channel: 'system', data: {} });
        return;
      }

      if (message.type === 'pong') {
        this.lastHeartbeat = Date.now();
        return;
      }

      // Route message to subscribers
      const channelSubscribers = this.subscriptions.get(message.channel);
      if (channelSubscribers) {
        channelSubscribers.forEach(callback => {
          try {
            callback(message.data);
          } catch (error) {
            console.error('Error in subscription callback:', error);
            this.eventHandlers.onError?.(error as Error);
          }
        });
      }

      this.eventHandlers.onMessage?.(message);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      this.eventHandlers.onError?.(error as Error);
    }
  }

  private handleClose(event: CloseEvent): void {
    this.cleanup();
    this.state = 'disconnected';
    this.connectionStats.totalDisconnections++;
    this.connectionStats.lastDisconnected = Date.now();
    this.notifyStateChange();

    // Only attempt reconnection if it wasn't a clean close
    if (event.code !== 1000 && this.reconnectAttempt < this.reconnectionConfig.maxAttempts) {
      this.scheduleReconnection();
    }

    this.eventHandlers.onDisconnect?.(event);
  }

  private handleError(error: Event): void {
    console.error('WebSocket error:', error);
    this.eventHandlers.onError?.(new Error('WebSocket connection error'));
  }

  private handleConnectionError(error: unknown): void {
    console.error('Connection establishment failed:', error);
    
    if (this.reconnectAttempt < this.reconnectionConfig.maxAttempts) {
      this.scheduleReconnection();
    } else {
      this.state = 'disconnected';
      this.notifyStateChange();
      this.eventHandlers.onError?.(new Error('Max reconnection attempts exceeded'));
    }
  }

  private scheduleReconnection(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempt++;
    this.connectionStats.totalReconnections++;

    const delay = this.calculateReconnectDelay();
    
    this.reconnectTimer = setTimeout(async () => {
      if (this.isOnline && this.circuitBreaker.canAttemptConnection()) {
        try {
          await this.connect();
        } catch (error) {
          // Error handling is done in connect method
        }
      } else {
        // If offline or circuit breaker is open, schedule another attempt
        this.scheduleReconnection();
      }
    }, delay);
  }

  private calculateReconnectDelay(): number {
    const exponentialDelay = this.reconnectionConfig.baseDelay * 
      Math.pow(this.reconnectionConfig.backoffMultiplier, this.reconnectAttempt - 1);
    
    const jitter = exponentialDelay * this.reconnectionConfig.jitterFactor * Math.random();
    const delayWithJitter = exponentialDelay + jitter;
    
    return Math.min(delayWithJitter, this.reconnectionConfig.maxDelay);
  }

  private startHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }

    // Send ping every 30 seconds
    this.pingInterval = setInterval(() => {
      if (this.state === 'connected') {
        this.send({ type: 'ping', channel: 'system', data: { timestamp: Date.now() } });
      }
    }, 30000);

    // Check for missed heartbeats every 10 seconds
    this.heartbeatTimer = setInterval(() => {
      if (this.state === 'connected' && Date.now() - this.lastHeartbeat > 60000) {
        console.warn('Heartbeat timeout - reconnecting');
        this.ws?.close();
      }
    }, 10000);
  }

  private cleanup(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = undefined;
    }

    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = undefined;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    this.ws = null;
  }

  private processQueuedMessages(): void {
    const queuedMessages = this.messageQueue.dequeueAll();
    queuedMessages.forEach(message => {
      this.send(message.message);
    });
  }

  subscribe(channel: string, callback: (message: any) => void, options?: SubscriptionOptions): void {
    if (!this.subscriptions.has(channel)) {
      this.subscriptions.set(channel, new Set());
    }

    this.subscriptions.get(channel)!.add(callback);

    // Send subscription message if connected
    if (this.state === 'connected') {
      this.send({
        type: 'subscribe',
        channel: 'subscriptions',
        data: {
          action: 'subscribe',
          channel,
          options: options || {},
        },
      });
    }
  }

  unsubscribe(channel: string, callback?: (message: any) => void): void {
    const channelSubscribers = this.subscriptions.get(channel);
    if (!channelSubscribers) return;

    if (callback) {
      channelSubscribers.delete(callback);
      if (channelSubscribers.size === 0) {
        this.subscriptions.delete(channel);
      }
    } else {
      this.subscriptions.delete(channel);
    }

    // Send unsubscription message if connected
    if (this.state === 'connected' && (!callback || channelSubscribers?.size === 0)) {
      this.send({
        type: 'unsubscribe',
        channel: 'subscriptions',
        data: {
          action: 'unsubscribe',
          channel,
        },
      });
    }
  }

  send(message: any): boolean {
    if (this.state === 'connected' && this.ws) {
      try {
        this.ws.send(JSON.stringify(message));
        this.connectionStats.messagesSent++;
        return true;
      } catch (error) {
        console.error('Error sending WebSocket message:', error);
        this.eventHandlers.onError?.(error as Error);
        
        // Queue message for retry
        this.messageQueue.enqueue({
          message,
          channel: message.channel || 'unknown',
          timestamp: Date.now(),
        });
        
        return false;
      }
    } else {
      // Queue message if not connected
      this.messageQueue.enqueue({
        message,
        channel: message.channel || 'unknown',
        timestamp: Date.now(),
      });
      
      // Try to reconnect if offline
      if (this.state === 'disconnected' && this.isOnline) {
        this.connect().catch(() => {
          // Error handling is done in connect method
        });
      }
      
      return false;
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = undefined;
    }

    this.reconnectAttempt = this.reconnectionConfig.maxAttempts; // Prevent reconnection

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
    }

    this.cleanup();
    this.state = 'disconnected';
    this.notifyStateChange();
  }

  getState(): WebSocketState {
    return this.state;
  }

  setEventHandlers(handlers: Partial<WebSocketEventHandlers>): void {
    this.eventHandlers = { ...this.eventHandlers, ...handlers };
  }

  getStats() {
    return {
      ...this.connectionStats,
      currentState: this.state,
      reconnectAttempt: this.reconnectAttempt,
      subscriptionCount: this.subscriptions.size,
      queueStats: this.messageQueue.getStats(),
      circuitBreakerState: this.circuitBreaker.getState(),
      isOnline: this.isOnline,
      connectionId: this.connectionId,
      lastHeartbeat: this.lastHeartbeat,
    };
  }

  // Force reconnection (for manual retry)
  async forceReconnect(): Promise<void> {
    this.disconnect();
    this.reconnectAttempt = 0;
    this.circuitBreaker = new WebSocketCircuitBreaker({
      failureThreshold: 5,
      resetTimeout: 60000,
      healthCheckInterval: 10000,
    });
    await this.connect();
  }

  private notifyStateChange(): void {
    this.eventHandlers.onStateChange?.(this.state);
  }

  destroy(): void {
    this.disconnect();
    this.circuitBreaker.destroy();
    window.removeEventListener('online', () => {});
    window.removeEventListener('offline', () => {});
    window.removeEventListener('beforeunload', () => {});
  }
}

// Global WebSocket manager instance
let globalWebSocketManager: MultiplexedWebSocketManager | null = null;

export function getWebSocketManager(config?: WebSocketConfig): MultiplexedWebSocketManager {
  if (!globalWebSocketManager && config) {
    globalWebSocketManager = new MultiplexedWebSocketManager(config);
  }
  
  if (!globalWebSocketManager) {
    throw new Error('WebSocket manager not initialized. Please provide config on first call.');
  }
  
  return globalWebSocketManager;
}

export function destroyWebSocketManager(): void {
  if (globalWebSocketManager) {
    globalWebSocketManager.destroy();
    globalWebSocketManager = null;
  }
} 