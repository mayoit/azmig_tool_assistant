import { Card, CardContent, Typography, Box, CircularProgress } from '@mui/material';
import type { SvgIconComponent } from '@mui/icons-material';

interface StatisticsCardProps {
  title: string;
  value: number | string;
  icon: SvgIconComponent;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  isLoading?: boolean;
  subtitle?: string;
}

export default function StatisticsCard({
  title,
  value,
  icon: Icon,
  color = 'primary',
  isLoading = false,
  subtitle,
}: StatisticsCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="text.secondary" variant="subtitle2" gutterBottom>
              {title}
            </Typography>
            {isLoading ? (
              <CircularProgress size={24} />
            ) : (
              <Typography variant="h4" component="div" fontWeight="bold">
                {value}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              bgcolor: `${color}.light`,
              color: `${color}.main`,
              borderRadius: 2,
              p: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Icon sx={{ fontSize: 32 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
