/**
 * WebSocket service for real-time progress updates
 */

import { ProcessingStatus, WebSocketMessage } from '../types';

export type WebSocketEventHandler = (status: ProcessingStatus) => void;
export type WebSocketErrorHandler = (error: string) => void;
export type WebSocketCloseHandler = () => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private alertId: string | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000; // Start with 1 second

  // Event handlers
  private onStatusUpdate: WebSocketEventHandler | null = null;
  private onError: WebSocketErrorHandler | null = null;
  private onClose: WebSocketCloseHandler | null = null;

  constructor() {
    this.handleMessage = this.handleMessage.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleClose = this.handleClose.bind(this);
  }

  /**
   * Connect to WebSocket for a specific alert
   */
  connect(alertId: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.alertId = alertId;
        const wsUrl = `ws://localhost:8000/ws/${alertId}`;
        
        console.log(`Connecting to WebSocket: ${wsUrl}`);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = this.handleMessage;
        this.ws.onerror = this.handleError;
        this.ws.onclose = this.handleClose;

        // Timeout for connection
        setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            reject(new Error('WebSocket connection timeout'));
          }
        }, 5000);

      } catch (error) {
        console.error('Error creating WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent) {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      console.log('WebSocket message received:', message);

      switch (message.type) {
        case 'status_update':
          if (message.data && this.onStatusUpdate) {
            this.onStatusUpdate(message.data);
          }
          break;
        case 'error':
          if (message.message && this.onError) {
            this.onError(message.message);
          }
          break;
        default:
          console.log('Unknown message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket errors
   */
  private handleError(event: Event) {
    console.error('WebSocket error:', event);
    if (this.onError) {
      this.onError('WebSocket connection error');
    }
  }

  /**
   * Handle WebSocket close
   */
  private handleClose(event: CloseEvent) {
    console.log('WebSocket closed:', event);
    
    if (this.onClose) {
      this.onClose();
    }

    // Attempt to reconnect if not intentionally closed
    if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
      this.attemptReconnect();
    }
  }

  /**
   * Attempt to reconnect WebSocket
   */
  private attemptReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
    
    setTimeout(() => {
      if (this.alertId) {
        this.connect(this.alertId).catch(error => {
          console.error('Reconnection failed:', error);
        });
      }
    }, delay);
  }

  /**
   * Set status update handler
   */
  onStatusUpdateHandler(handler: WebSocketEventHandler) {
    this.onStatusUpdate = handler;
  }

  /**
   * Set error handler
   */
  onErrorHandler(handler: WebSocketErrorHandler) {
    this.onError = handler;
  }

  /**
   * Set close handler
   */
  onCloseHandler(handler: WebSocketCloseHandler) {
    this.onClose = handler;
  }

  /**
   * Send a message through WebSocket
   */
  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not open. Cannot send message:', message);
    }
  }

  /**
   * Close WebSocket connection
   */
  disconnect() {
    if (this.ws) {
      console.log('Closing WebSocket connection');
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.alertId = null;
    this.reconnectAttempts = 0;
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export default WebSocketService; 