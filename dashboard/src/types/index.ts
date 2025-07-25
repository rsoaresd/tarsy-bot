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

// Alert list component props
export interface AlertListProps {
  loading?: boolean;
  error?: string | null;
  sessions?: Session[];
  onRefresh?: () => void;
}

// Individual alert list item props
export interface AlertListItemProps {
  session: Session;
  onClick?: (sessionId: string) => void;
} 