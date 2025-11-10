export interface ValidationJob {
  id: number;
  project_id: number;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  celery_task_id?: string;
  total_items: number;
  processed_items: number;
  passed_items: number;
  warning_items: number;
  failed_items: number;
  error_message?: string;
  error_details?: Record<string, unknown>;
  created_by_id: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ValidationResult {
  id: number;
  job_id: number;
  server_id: number;
  validation_stage: string;
  passed: boolean;
  message?: string;
  details?: string;
  created_at: string;
  server_name?: string;
}

export interface ValidationStatusUpdate {
  job_id: number;
  status: string;
  progress: number;
  message: string;
}

export interface ValidationEvent {
  id: number;
  validation_job_id: number;
  project_id: number;
  event_name: string;
  event_category: string;
  validation_type: string;
  resource_type?: string;
  resource_name?: string;
  resource_id?: string;
  status: 'passed' | 'failed' | 'warning' | 'skipped';
  operation_status: string; // Started, InProgress, Completed, Failed
  message?: string;
  details?: Record<string, unknown>;
  error_message?: string;
  request_payload?: Record<string, unknown>;
  response_payload?: Record<string, unknown>;
  event_timestamp: string;
  submitted_at?: string;
  completed_at?: string;
  duration_ms?: number;
}
