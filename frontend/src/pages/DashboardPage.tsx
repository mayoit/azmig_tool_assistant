import { Box, Typography, Alert, CircularProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { 
  FolderOpen as ProjectIcon,
  CheckCircle as SuccessIcon,
  Storage as StorageIcon,
  Assessment as ValidationIcon,
} from '@mui/icons-material';
import StatisticsCard from '../components/dashboard/StatisticsCard';
import RecentJobs from '../components/dashboard/RecentJobs';
import ValidationChart from '../components/dashboard/ValidationChart';
import QuickActions from '../components/dashboard/QuickActions';
import dashboardService from '../services/dashboard.service';

export default function DashboardPage() {
  // Fetch dashboard data
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardService.getDashboardData(),
  });

  const stats = dashboardData?.stats;
  const recentJobs = dashboardData?.recent_jobs || [];
  const trends = dashboardData?.trends || [];

  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Overview of your migration projects and validation status
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load dashboard data. Please try again.
        </Alert>
      )}

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Statistics Cards */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                sm: 'repeat(2, 1fr)',
                md: 'repeat(4, 1fr)',
              },
              gap: 3,
              mb: 4,
            }}
          >
            <StatisticsCard
              title="Total Projects"
              value={stats?.total_projects || 0}
              icon={ProjectIcon}
              color="primary"
              isLoading={false}
              subtitle={`${stats?.active_projects || 0} active`}
            />

            <StatisticsCard
              title="Active Projects"
              value={stats?.active_projects || 0}
              icon={SuccessIcon}
              color="success"
              isLoading={false}
              subtitle="Currently active"
            />

            <StatisticsCard
              title="Total Servers"
              value={stats?.total_servers || 0}
              icon={StorageIcon}
              color="warning"
              isLoading={false}
              subtitle="Ready for migration"
            />

            <StatisticsCard
              title="Total Validations"
              value={stats?.total_validations || 0}
              icon={ValidationIcon}
              color="info"
              isLoading={false}
              subtitle="Jobs completed"
            />
          </Box>

          {/* Quick Actions */}
          <Box sx={{ mb: 4 }}>
            <QuickActions stats={stats || { total_projects: 0, active_projects: 0, total_servers: 0, total_validations: 0 }} />
          </Box>

          {/* Recent Jobs and Trends */}
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: {
                xs: '1fr',
                lg: 'repeat(2, 1fr)',
              },
              gap: 3,
            }}
          >
            <RecentJobs jobs={recentJobs} />
            <ValidationChart trends={trends} />
          </Box>
        </>
      )}
    </Box>
  );
}
