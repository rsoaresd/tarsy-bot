// Basic alert session types for Phase 1
export interface Session {
  session_id: string;
  alert_id: string;
  alert_type: string;
  agent_type: string;
  status: 'completed' | 'failed' | 'in_progress' | 'pending';
  started_at: string; // ISO timestamp
  completed_at: string | null;
  duration_ms: number | null;
  summary?: string | object; // Backend may return string or empty object
  error_message: string | null;
  llm_interaction_count?: number;
  mcp_communication_count?: number;
}

// Phase 3: Detailed session data for session detail page
export interface DetailedSession extends Session {
  alert_data: AlertData;
  final_analysis: string | null;
  chronological_timeline: TimelineItem[];
}

// Phase 3: Original alert data structure
export interface AlertData {
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: string; // ISO timestamp
  environment: 'development' | 'staging' | 'production';
  cluster: string;
  namespace: string;
  pod?: string;
  context?: string;
  runbook?: string;
}

// Phase 3: Timeline item structure
export interface TimelineItem {
  id: string;
  event_id: string;
  type: 'llm' | 'mcp' | 'system';
  timestamp: string; // ISO timestamp with microseconds
  step_description: string;
  duration_ms: number | null;
  details?: LLMInteraction | MCPInteraction | SystemEvent;
}

// Phase 3: LLM interaction details
export interface LLMInteraction {
  prompt: string;
  response: string;
  model_name: string;
  tokens_used?: number;
  temperature?: number;
}

// Phase 3: MCP interaction details
export interface MCPInteraction {
  tool_name: string;
  parameters: Record<string, any>;
  result: any;
  server_name: string;
  execution_time_ms: number;
}

// Phase 3: System event details
export interface SystemEvent {
  event_type: string;
  description: string;
  metadata?: Record<string, any>;
}

// Pagination information from backend
export interface Pagination {
  page: number;
  page_size: number;
  total_pages: number;
  total_items: number;
}

// Filters applied (for future phases)
export interface FiltersApplied {
  [key: string]: any;
}

// Sessions endpoint response (actual backend format)
export interface SessionsResponse {
  sessions: Session[];
  pagination: Pagination;
  filters_applied: FiltersApplied;
}

// WebSocket message types (Phase 2)
export interface WebSocketMessage {
  type: 'session_update' | 'session_completed' | 'session_failed' | 'ping' | 'pong' | 'connection_established' | 'subscription_response' | 'dashboard_update';
  data?: SessionUpdate | any; // Allow any data type for dashboard_update messages
  timestamp?: string;
  channel?: string; // Dashboard updates include channel info
}

export interface SessionUpdate {
  session_id: string;
  status: Session['status'];
  progress?: number; // 0-100 for in_progress sessions
  duration_ms?: number;
  error_message?: string | null;
  completed_at?: string | null;
}

// API response wrapper format (for other endpoints)
export interface APIResponse<T> {
  data: T;
  error?: string;
  timestamp?: string;
}

// Status badge props
export interface StatusBadgeProps {
  status: Session['status'];
  size?: 'small' | 'medium';
}

// Alert list component props (Phase 1)
export interface AlertListProps {
  loading?: boolean;
  error?: string | null;
  sessions?: Session[];
  onRefresh?: () => void;
}

// Individual alert list item props (Phase 1)
export interface AlertListItemProps {
  session: Session;
  onClick?: (sessionId: string) => void;
}

// Active alerts panel props (Phase 2)
export interface ActiveAlertsPanelProps {
  sessions?: Session[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onSessionClick?: (sessionId: string) => void;
}

// Active alert card props (Phase 2)
export interface ActiveAlertCardProps {
  session: Session;
  progress?: number;
  onClick?: (sessionId: string) => void;
}

// Historical alerts list props (Phase 2)
export interface HistoricalAlertsListProps {
  sessions?: Session[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onSessionClick?: (sessionId: string) => void;
}

// Dashboard layout props (Phase 2)
export interface DashboardLayoutProps {
  activeAlerts: Session[];
  historicalAlerts: Session[];
  activeLoading?: boolean;
  historicalLoading?: boolean;
  activeError?: string | null;
  historicalError?: string | null;
  onRefreshActive?: () => void;
  onRefreshHistorical?: () => void;
  onSessionClick?: (sessionId: string) => void;
}

// Phase 3: Session detail page props
export interface SessionDetailPageProps {
  sessionId: string;
}

// Phase 3: Session header props
export interface SessionHeaderProps {
  session: DetailedSession;
}

// Phase 3: Original alert card props
export interface OriginalAlertCardProps {
  alertData: AlertData;
}

// Phase 3: Final analysis card props
export interface FinalAnalysisCardProps {
  analysis: string | null;
  sessionStatus: Session['status'];
  errorMessage?: string | null;
}

// Phase 3: Timeline props
export interface SimpleTimelineProps {
  timelineItems: TimelineItem[];
}

// Phase 3: Back button props
export interface BackButtonProps {
  onClick: () => void;
} 