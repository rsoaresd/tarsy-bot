/**
 * React hooks for WebSocket state management
 * Provides easy-to-use interface for dashboard components
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getWebSocketManager, destroyWebSocketManager } from '../services/WebSocketManager';
import { WebSocketConfig, WebSocketState, SubscriptionOptions } from '../types/websocket';

// Global WebSocket manager configuration
const defaultConfig: WebSocketConfig = {
  url: process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/dashboard',
  userId: 'anonymous', // This should be set from auth context
  connectionTimeout: 10000,
  messageTimeout: 5000,
  reconnection: {
    maxAttempts: 10,
    baseDelay: 1000,
    maxDelay: 30000,
    backoffMultiplier: 1.5,
    jitterFactor: 0.3,
  },
};

// Initialize global WebSocket manager
let wsManager: ReturnType<typeof getWebSocketManager> | null = null;

function initializeWebSocketManager() {
  if (!wsManager) {
    wsManager = getWebSocketManager(defaultConfig);
  }
  return wsManager;
}

// Enhanced WebSocket hook with error handling and retry mechanisms
export function useWebSocket() {
  const [state, setState] = useState<WebSocketState>('disconnected');
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [stats, setStats] = useState<any>(null);
  const managerRef = useRef<ReturnType<typeof getWebSocketManager> | null>(null);

  useEffect(() => {
    const manager = initializeWebSocketManager();
    managerRef.current = manager;

    // Set up event handlers
    manager.setEventHandlers({
      onConnect: () => {
        setState('connected');
        setIsConnected(true);
        setError(null);
      },
      onDisconnect: () => {
        setState('disconnected');
        setIsConnected(false);
      },
      onError: (error: Error) => {
        setError(error);
      },
      onMessage: (message) => {
        // Handle global messages if needed
      },
    });

    // Update stats periodically
    const statsInterval = setInterval(() => {
      setStats(manager.getStats());
    }, 5000);

    // Initial connection attempt
    manager.connect().catch((error) => {
      console.warn('Initial WebSocket connection failed:', error);
      setError(error);
    });

    return () => {
      clearInterval(statsInterval);
      // Don't destroy the manager here as it's shared
    };
  }, []);

  const forceReconnect = useCallback(async () => {
    if (managerRef.current) {
      try {
        setError(null);
        await managerRef.current.forceReconnect();
      } catch (error) {
        setError(error as Error);
        throw error;
      }
    }
  }, []);

  const disconnect = useCallback(() => {
    if (managerRef.current) {
      managerRef.current.disconnect();
    }
  }, []);

  return {
    state,
    isConnected,
    error,
    stats,
    forceReconnect,
    disconnect,
    manager: managerRef.current,
  };
}

// Enhanced WebSocket subscription hook with error handling
export function useWebSocketSubscription<T>(
  channel: string,
  onMessage: (message: T) => void,
  options?: {
    retryOnError?: boolean;
    maxRetries?: number;
    enabled?: boolean;
    autoResubscribe?: boolean;
    bufferMessages?: boolean;
    maxBuffer?: number;
    priority?: 'high' | 'normal' | 'low';
  }
) {
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const { isConnected, manager } = useWebSocket();
  const optionsRef = useRef(options);
  const onMessageRef = useRef(onMessage);
  const retryTimeoutRef = useRef<NodeJS.Timeout>();

  // Update refs when props change
  useEffect(() => {
    optionsRef.current = options;
    onMessageRef.current = onMessage;
  }, [options, onMessage]);

  const subscribe = useCallback(() => {
    if (!manager || !isConnected || optionsRef.current?.enabled === false) {
      return;
    }

    try {
             manager.subscribe(
         channel,
         (message: T) => {
           try {
             onMessageRef.current(message);
             setError(null);
             setRetryCount(0);
           } catch (error) {
             console.error('Error in message handler:', error);
             setError((error as Error).message);
           }
         },
         {
           autoResubscribe: optionsRef.current?.autoResubscribe,
           bufferMessages: optionsRef.current?.bufferMessages,
           maxBuffer: optionsRef.current?.maxBuffer,
           priority: optionsRef.current?.priority,
         }
       );
      
      setIsSubscribed(true);
      setError(null);
    } catch (error) {
      console.error('Subscription failed:', error);
      setError((error as Error).message);
      
      // Retry subscription if enabled
      if (optionsRef.current?.retryOnError && retryCount < (optionsRef.current?.maxRetries || 3)) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        retryTimeoutRef.current = setTimeout(() => {
          setRetryCount(prev => prev + 1);
          subscribe();
        }, delay);
      }
    }
  }, [manager, isConnected, channel, retryCount]);

  const unsubscribe = useCallback(() => {
    if (manager) {
      manager.unsubscribe(channel);
      setIsSubscribed(false);
      setRetryCount(0);
    }
    
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
      retryTimeoutRef.current = undefined;
    }
  }, [manager, channel]);

  useEffect(() => {
    if (isConnected && optionsRef.current?.enabled !== false) {
      subscribe();
    } else {
      setIsSubscribed(false);
    }

    return () => {
      unsubscribe();
    };
  }, [isConnected, subscribe, unsubscribe]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, []);

  return {
    isSubscribed,
    error,
    subscribe,
    unsubscribe,
    retryCount,
  };
}

// Enhanced dashboard updates hook with error handling and offline support
export function useDashboardUpdates(
  onUpdate?: (updateData: any) => void,
  options?: { enabled?: boolean; retryOnError?: boolean }
) {
  const [updates, setUpdates] = useState<any>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const onUpdateRef = useRef(onUpdate);

  // Update ref when prop changes
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  const handleMessage = useCallback((updateData: any) => {
    try {
      setUpdates(updateData);
      setLastUpdateTime(new Date());
      setError(null);
      onUpdateRef.current?.(updateData);
    } catch (error) {
      console.error('Error processing dashboard update:', error);
      setError((error as Error).message);
    }
  }, []);

     const {
     isSubscribed,
     error: subscriptionError,
     retryCount,
   } = useWebSocketSubscription(
     'dashboard_updates',
     handleMessage,
     {
       enabled: options?.enabled,
       retryOnError: options?.retryOnError ?? true,
       maxRetries: 5,
       priority: 'high',
     }
   );

  return {
    isSubscribed,
    updates,
    lastUpdateTime,
    error: error || subscriptionError,
    retryCount,
  };
}

// Enhanced session updates hook with error handling
export function useSessionUpdates(
  sessionId: string,
  onUpdate?: (updateData: any) => void,
  options?: { enabled?: boolean; retryOnError?: boolean }
) {
  const [updates, setUpdates] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const onUpdateRef = useRef(onUpdate);

  // Update ref when prop changes
  useEffect(() => {
    onUpdateRef.current = onUpdate;
  }, [onUpdate]);

  const handleMessage = useCallback((updateData: any) => {
    try {
      setUpdates(updateData);
      setError(null);
      onUpdateRef.current?.(updateData);
    } catch (error) {
      console.error('Error processing session update:', error);
      setError((error as Error).message);
    }
  }, []);

     const {
     isSubscribed,
     error: subscriptionError,
     subscribe,
     unsubscribe,
     retryCount,
   } = useWebSocketSubscription(
     `session_${sessionId}`,
     handleMessage,
     {
       enabled: options?.enabled && !!sessionId,
       retryOnError: options?.retryOnError ?? true,
       maxRetries: 3,
       priority: 'normal',
     }
   );

  return {
    isSubscribed,
    updates,
    error: error || subscriptionError,
    subscribe,
    unsubscribe,
    retryCount,
  };
}

// Enhanced system health hook with error handling
export function useSystemHealth(
  onHealthUpdate?: (healthData: any) => void,
  options?: { enabled?: boolean; retryOnError?: boolean }
) {
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const onHealthUpdateRef = useRef(onHealthUpdate);

  // Update ref when prop changes
  useEffect(() => {
    onHealthUpdateRef.current = onHealthUpdate;
  }, [onHealthUpdate]);

  const handleMessage = useCallback((healthData: any) => {
    try {
      setHealth(healthData);
      setError(null);
      onHealthUpdateRef.current?.(healthData);
    } catch (error) {
      console.error('Error processing health update:', error);
      setError((error as Error).message);
    }
  }, []);

     const {
     isSubscribed,
     error: subscriptionError,
     retryCount,
   } = useWebSocketSubscription(
     'system_health',
     handleMessage,
     {
       enabled: options?.enabled,
       retryOnError: options?.retryOnError ?? true,
       maxRetries: 3,
       priority: 'low',
     }
   );

  return {
    isSubscribed,
    health,
    error: error || subscriptionError,
    retryCount,
  };
}

// WebSocket status hook with enhanced error reporting
export function useWebSocketStatus() {
  const webSocketHook = useWebSocket();
  
  return {
    ...webSocketHook,
    isHealthy: webSocketHook.isConnected && !webSocketHook.error,
    canRetry: webSocketHook.state === 'disconnected' && navigator.onLine,
  };
}

// Cleanup hook for component unmounting
export function useWebSocketCleanup() {
  useEffect(() => {
    return () => {
      // Only destroy the manager if we're the last component using it
      // In a real app, you'd want more sophisticated cleanup logic
      if (process.env.NODE_ENV === 'development') {
        console.log('WebSocket cleanup - manager still active');
      }
    };
  }, []);
}

// Error recovery hook
export function useWebSocketErrorRecovery() {
  const { error, forceReconnect, isConnected } = useWebSocket();
  const [isRecovering, setIsRecovering] = useState(false);
  const [recoveryAttempts, setRecoveryAttempts] = useState(0);

  const attemptRecovery = useCallback(async () => {
    if (isRecovering || isConnected || recoveryAttempts >= 3) {
      return;
    }

    setIsRecovering(true);
    setRecoveryAttempts(prev => prev + 1);

    try {
      await forceReconnect();
      setRecoveryAttempts(0);
    } catch (error) {
      console.error('Recovery attempt failed:', error);
    } finally {
      setIsRecovering(false);
    }
  }, [isRecovering, isConnected, recoveryAttempts, forceReconnect]);

  // Reset recovery attempts when connection is restored
  useEffect(() => {
    if (isConnected) {
      setRecoveryAttempts(0);
      setIsRecovering(false);
    }
  }, [isConnected]);

  return {
    error,
    isRecovering,
    recoveryAttempts,
    canRecover: !isConnected && !isRecovering && recoveryAttempts < 3 && navigator.onLine,
    attemptRecovery,
  };
} 