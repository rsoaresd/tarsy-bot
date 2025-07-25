// Basic alert session types for Phase 1
export interface Session {
  id: string;
  alert_type: string;
  agent_type: string;
  status: 'completed' | 'failed' | 'in_progress' | 'pending';
  started_at: string; // ISO timestamp
  completed_at: string | null;
  duration_ms: number | null;
  summary: string;
  error_message: string | null;
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