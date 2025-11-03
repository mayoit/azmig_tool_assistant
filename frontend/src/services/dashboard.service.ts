import api from './api';

export interface DashboardStats {
  total_projects: number;
  active_projects: number;
  total_servers: number;
  total_validations: number;
}

export interface RecentValidationJob {
  id: number;
  project_id: number;
  project_name: string;
  status: string;
  job_type: string;
  created_at: string;
  completed_at?: string | null;
}

export interface ValidationTrend {
  date: string; // ISO format date (YYYY-MM-DD)
  passed: number;
  failed: number;
  total: number;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_jobs: RecentValidationJob[];
  trends: ValidationTrend[];
}

const dashboardService = {
  /**
   * Fetch dashboard data including stats, recent jobs, and validation trends
   */
  getDashboardData: async (): Promise<DashboardData> => {
    const response = await api.get<DashboardData>('/dashboard');
    return response.data;
  },
};

export default dashboardService;
