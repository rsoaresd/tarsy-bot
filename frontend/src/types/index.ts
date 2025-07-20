/**
 * TypeScript type definitions for the SRE AI Agent frontend
 */

export interface Alert {
  alert_type: string;
  severity: string;
  environment: string;
  cluster: string;
  namespace: string;
  pod?: string;
  message: string;
  runbook: string;
  context?: string;
  timestamp?: string;
}

export interface AlertResponse {
  alert_id: string;
  status: string;
  message: string;
}

export interface ProcessingStatus {
  alert_id: string;
  status: 'queued' | 'processing' | 'completed' | 'error';
  progress: number;
  current_step: string;
  result?: string;
  error?: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'status_update' | 'error' | 'connected';
  data?: ProcessingStatus;
  message?: string;
}

export interface AlertFormData {
  alert_type: string;
  severity: string;
  environment: string;
  cluster: string;
  namespace: string;
  pod: string;
  message: string;
  runbook: string;
  context: string;
}

export interface AlertTypeOption {
  value: string;
  label: string;
}

export interface SeverityOption {
  value: string;
  label: string;
}

export interface EnvironmentOption {
  value: string;
  label: string;
} 