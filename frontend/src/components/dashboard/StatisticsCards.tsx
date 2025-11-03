import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material';
import {
  FolderOutlined,
  PlayCircleOutlineOutlined,
  CheckCircleOutlineOutlined,
  TrendingUpOutlined,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { projectsService } from '../../services/projects.service';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: string;
}

const StatCard = ({ title, value, icon, color, trend }: StatCardProps) => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Typography color="text.secondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" fontWeight="bold" mb={1}>
              {value}
            </Typography>
            {trend && (
              <Box display="flex" alignItems="center" gap={0.5}>
                <TrendingUpOutlined sx={{ fontSize: 16, color: 'success.main' }} />
                <Typography variant="caption" color="success.main">
                  {trend}
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              bgcolor: `${color}.lighter`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: `${color}.main`,
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

const StatCardSkeleton = () => {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box flex={1}>
            <Skeleton variant="text" width={100} height={20} />
            <Skeleton variant="text" width={80} height={48} sx={{ mt: 1 }} />
            <Skeleton variant="text" width={60} height={16} sx={{ mt: 1 }} />
          </Box>
          <Skeleton variant="rounded" width={56} height={56} />
        </Box>
      </CardContent>
    </Card>
  );
};

export const StatisticsCards = () => {
  const { data: projectsData, isLoading } = useQuery({
    queryKey: ['projects', { page: 1, limit: 100 }],
    queryFn: () => projectsService.getAll({ page: 1, limit: 100 }),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
        {[1, 2, 3, 4].map((i) => (
          <StatCardSkeleton key={i} />
        ))}
      </Box>
    );
  }

  const projects = projectsData?.items || [];
  const totalProjects = projectsData?.total || 0;
  const activeProjects = projects.filter((p) => p.status === 'active').length;
  const completedProjects = projects.filter((p) => p.status === 'completed').length;

  // Calculate success rate (active + completed out of total)
  const successRate = totalProjects > 0 
    ? Math.round(((activeProjects + completedProjects) / totalProjects) * 100) 
    : 0;

  return (
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 3, mb: 3 }}>
      <StatCard
        title="Total Projects"
        value={totalProjects}
        icon={<FolderOutlined fontSize="large" />}
        color="primary"
      />

      <StatCard
        title="Active Projects"
        value={activeProjects}
        icon={<PlayCircleOutlineOutlined fontSize="large" />}
        color="info"
        trend={activeProjects > 0 ? `${activeProjects} in progress` : undefined}
      />

      <StatCard
        title="Completed Projects"
        value={completedProjects}
        icon={<CheckCircleOutlineOutlined fontSize="large" />}
        color="success"
      />

      <StatCard
        title="Success Rate"
        value={`${successRate}%`}
        icon={<TrendingUpOutlined fontSize="large" />}
        color="warning"
        trend={successRate >= 80 ? 'Excellent' : successRate >= 60 ? 'Good' : 'Needs attention'}
      />
    </Box>
  );
};
