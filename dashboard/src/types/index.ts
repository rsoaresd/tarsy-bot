/**
 * Dashboard TypeScript type definitions
 * Following EP-0004 specifications for data models and UI components
 */

export interface SessionSummary {
  session_id: string;
  status: 'active' | 'completed' | 'error' | 'timeout';
  agent_type?: string;
  start_time?: string;
  last_activity?: string;
  interactions_count: number;
  llm_interactions: number;
  mcp_communications: number;
  errors_count: number;
  current_step?: string;
  progress_percentage: number;
}

export interface AlertStatus {
  alert_id: string;
  status: 'processing' | 'completed' | 'failed' | 'pending';
  progress: number;
  current_step: string;
  current_agent?: string;
  assigned_mcp_servers?: string[];
  result?: string;
  error?: string;
  session_id?: string;
}

export interface DashboardMetrics {
  active_sessions: number;
  completed_sessions: number;
  failed_sessions: number;
  total_interactions: number;
  avg_session_duration: number;
  error_rate: number;
  last_updated: string;
}

export interface InteractionDetail {
  interaction_id: string;
  interaction_type: 'llm' | 'mcp';
  session_id: string;
  step_description: string;
  timestamp: string;
  success: boolean;
  duration_ms: number;
  
  // LLM-specific fields
  model?: string;
  tokens_used?: number;
  
  // MCP-specific fields
  server_name?: string;
  communication_type?: string;
  tool_name?: string;
  tool_arguments?: Record<string, any>;
  
  error_message?: string;
}

export interface SessionTimeline {
  session_id: string;
  interactions: InteractionDetail[];
  summary: SessionSummary;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  timestamp?: string;
}

export interface SubscriptionMessage extends WebSocketMessage {
  type: 'subscribe' | 'unsubscribe';
  channel: string;
}

export interface DashboardUpdate extends WebSocketMessage {
  type: 'dashboard_update';
  data: Record<string, any>;
  channel: string;
}

export interface SessionUpdate extends WebSocketMessage {
  type: 'session_update';
  session_id: string;
  data: Record<string, any>;
  channel?: string;
}

export interface SystemHealthUpdate extends WebSocketMessage {
  type: 'system_health';
  status: 'healthy' | 'degraded' | 'unhealthy';
  services: Record<string, any>;
  channel: string;
}

// Filter and Search Types
export interface SessionFilter {
  status?: string[];
  agent_type?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  search_query?: string;
}

export interface PaginationOptions {
  page: number;
  per_page: number;
  total: number;
}

// UI State Types
export interface DashboardState {
  activeAlerts: AlertStatus[];
  historicalSessions: SessionSummary[];
  metrics: DashboardMetrics;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  lastUpdate: string;
}

export interface ViewOptions {
  showActiveOnly: boolean;
  expandedCards: Set<string>;
  selectedSession?: string;
  filters: SessionFilter;
  pagination: PaginationOptions;
} 