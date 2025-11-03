export interface ValidationJob {
  id: number;
  project_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error_message?: string;
  created_at: string;
  updated_at: string;
  results_count?: number;
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
